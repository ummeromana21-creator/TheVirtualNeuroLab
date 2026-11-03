"""lif_engine.py - the lab's simulation engine: a whole-nervous-system leaky integrate-and-fire network.

It is a re-implementation of the published model of Shiu et al. 2024 (Nature 634:210,
"A Drosophila computational brain model reveals sensorimotor processing"; code:
github.com/philshiu/Drosophila_brain_model, model.py), with the same equations and the same numbers:

  every neuron:   dv/dt = (v0 - v + g) / t_mbr      dg/dt = -g / tau
                  (while refractory, v stays at reset and incoming input is lost, exactly as the published code
                  behaves when run in Brian2 2.x - verified step by step)
                  spike when v > v_th, then v = v_rst, g = 0, refractory for t_rfc
  every synapse:  a spike of neuron i adds  w_syn x (synapse count i->j) x sign(i)  to g of neuron j,
                  t_dly later. sign = -1 if neuron i releases GABA, glutamate (or histamine), else +1.
  stimulation:    'activated' neurons get Poisson kicks of w_syn x f_poi (enough to make them spike) at a
                  chosen rate, and have no refractory period (as in model.py).
  numbers:        v0 = v_rst = -52 mV, v_th = -45 mV, t_mbr = 20 ms, tau = 5 ms, t_rfc = 2.2 ms,
                  t_dly = 1.8 ms, w_syn = 0.275 mV, f_poi = 250, time step 0.1 ms, 1 s per trial,
                  30 trials. Nothing is tuned here: these are the paper's values.

Implementation: Brian2's 'linear' method integrates these equations exactly over each step; so does this
code (closed-form update). Neurons at rest with no input stay exactly at rest, so only neurons that have
ever been reached are updated: this is what makes a 140,000-160,000-neuron run take seconds.
All trials of one condition run side by side (one column per trial).
"""
import numpy as np
from scipy import sparse

P = dict(v0=-52.0, v_rst=-52.0, v_th=-45.0, t_mbr=20.0, tau=5.0, t_rfc=2.2, t_dly=1.8,
         w_syn=0.275, f_poi=250.0, dt=0.1, t_run=1000.0, n_run=30)
INHIBITORY = {'GABA', 'GLUT', 'GLU', 'HIST', 'HA'}


class Network:
    def __init__(self, ids, pre, post, syn, sign):
        """ids: neuron ids (length N). pre/post: indices into ids. syn: synapse counts. sign: +1/-1 per neuron."""
        self.ids = np.asarray(ids)
        self.N = len(self.ids)
        self.index = {int(k): i for i, k in enumerate(self.ids)}
        w = np.asarray(syn, dtype=np.float64) * np.asarray(sign, dtype=np.float64)[np.asarray(pre)]
        # rows = presynaptic neuron, so a spike of i reads row i
        self.W = sparse.csr_matrix((w, (np.asarray(pre), np.asarray(post))), shape=(self.N, self.N))
        self.W.sum_duplicates()

    def idx(self, ids):
        return np.array([self.index[int(i)] for i in ids if int(i) in self.index], dtype=np.int64)

    def run(self, groups, silence=(), p=None, seed=0, record=None, times=None):
        """groups: list of (neuron indices, rate in Hz). Returns spike counts per neuron per trial,
        as a dict {neuron index: array(n_run)} for every neuron that spiked (or `record`ed).
        times: optional list; if given, every spike of trial 0 is appended to it as (neuron index, time in ms)."""
        p = dict(P, **(p or {}))
        dt, T, nT = p['dt'], int(round(p['t_run'] / p['dt'])), int(p['n_run'])
        delay = int(round(p['t_dly'] / dt))
        a_m, a_s = np.exp(-dt / p['t_mbr']), np.exp(-dt / p['tau'])
        b = (a_m - a_s) * p['tau'] / (p['t_mbr'] - p['tau'])   # contribution of g to v over one step (exact)
        rfc_steps = p['t_rfc'] / dt
        kick = p['w_syn'] * p['f_poi']
        rng = np.random.default_rng(seed)
        W = self.W
        if len(silence):
            keep = np.ones(self.N); keep[np.asarray(silence)] = 0.0
            W = sparse.diags(keep) @ W @ sparse.diags(keep)
            W = W.tocsr()
        indptr, indices, data = W.indptr, W.indices, W.data * p['w_syn']

        # active set: local arrays for neurons ever reached; global -> local map
        loc = np.full(self.N, -1, dtype=np.int64)
        act = []                                       # local -> global
        def add(gidx):
            new = gidx[loc[gidx] < 0]
            new = np.unique(new)
            if len(new):
                loc[new] = np.arange(len(act), len(act) + len(new))
                act.extend(new.tolist())
            return len(new)
        stim = [(np.asarray(g, dtype=np.int64), float(r)) for g, r in groups if len(g)]
        for g, _ in stim:
            add(g)
        cap = 4096
        v = np.full((cap, nT), p['v0']); g_ = np.zeros((cap, nT)); ref = np.zeros((cap, nT))
        counts = np.zeros((cap, nT), dtype=np.int32)
        is_stim = np.zeros(cap, bool)
        for g, _ in stim:
            is_stim[loc[g]] = True
        ring = [[] for _ in range(delay + 1)]          # pending g increments: (global post idx, trial, value)

        for step in range(T):
            n = len(act)
            if n > cap:                                 # grow local arrays
                newcap = max(cap * 2, n + 1024)
                v = np.vstack([v, np.full((newcap - cap, nT), p['v0'])])
                g_ = np.vstack([g_, np.zeros((newcap - cap, nT))])
                ref = np.vstack([ref, np.zeros((newcap - cap, nT))])
                counts = np.vstack([counts, np.zeros((newcap - cap, nT), dtype=np.int32)])
                is_stim = np.concatenate([is_stim, np.zeros(newcap - cap, bool)])
                cap = newcap
            V, G, R = v[:n], g_[:n], ref[:n]
            # 1. state update (exact), frozen while refractory
            free = R <= 0
            Vn = p['v0'] + (V - p['v0']) * a_m + G * b
            V[free] = Vn[free]
            G[free] = (G * a_s)[free]
            G[~free] = 0.0                              # as in the published Brian2 code: input arriving while
            R[~free] -= 1                               # a neuron is refractory is lost (checked against Brian2)
            # 2. Poisson kicks to stimulated neurons
            for gi, rate in stim:
                if rate <= 0:
                    continue
                li = loc[gi]
                hit = rng.random((len(li), nT)) < rate * dt / 1000.0
                V[li] += hit * kick
            # 3. delivered synaptic input arriving this step
            slot = ring[step % (delay + 1)]
            if slot:
                post = np.concatenate([s[0] for s in slot]); tr = np.concatenate([s[1] for s in slot])
                val = np.concatenate([s[2] for s in slot])
                add(post)
                n = len(act)
                if n > cap:
                    newcap = max(cap * 2, n + 1024)
                    v = np.vstack([v, np.full((newcap - cap, nT), p['v0'])])
                    g_ = np.vstack([g_, np.zeros((newcap - cap, nT))])
                    ref = np.vstack([ref, np.zeros((newcap - cap, nT))])
                    counts = np.vstack([counts, np.zeros((newcap - cap, nT), dtype=np.int32)])
                    is_stim = np.concatenate([is_stim, np.zeros(newcap - cap, bool)])
                    cap = newcap
                G = g_[:n]
                flat = loc[post] * nT + tr
                G.ravel()[:] += np.bincount(flat, weights=val, minlength=n * nT)[: n * nT]
                ring[step % (delay + 1)] = []
                V, R = v[:n], ref[:n]
            # 4. threshold, reset, refractory
            sp = V > p['v_th']
            if sp.any():
                li, tr = np.nonzero(sp)
                counts[li, tr] += 1
                V[sp] = p['v_rst']; G[sp] = 0.0
                R[sp] = np.where(is_stim[li], 0.0, rfc_steps)
                gl = np.asarray(act, dtype=np.int64)[li]
                if times is not None:
                    z = tr == 0
                    times.extend(zip(gl[z].tolist(), [round(step * dt, 1)] * int(z.sum())))
                # 5. schedule synaptic effect t_dly later
                starts, ends = indptr[gl], indptr[gl + 1]
                lens = ends - starts
                if lens.sum():
                    rep = np.repeat(np.arange(len(gl)), lens)
                    off = np.arange(lens.sum()) - np.repeat(np.cumsum(lens) - lens, lens)
                    k = starts[rep] + off
                    ring[(step + delay) % (delay + 1)].append((indices[k].astype(np.int64), tr[rep], data[k]))
        n = len(act)
        out = {}
        actg = np.asarray(act, dtype=np.int64)
        tot = counts[:n].sum(1)
        for li in np.nonzero(tot)[0]:
            out[int(actg[li])] = counts[li].copy()
        for r in (record if record is not None else []):
            out.setdefault(int(r), np.zeros(nT, dtype=np.int32))
        return out   # spikes per trial (trial length = t_run ms, so spikes / s = Hz when t_run = 1000)
