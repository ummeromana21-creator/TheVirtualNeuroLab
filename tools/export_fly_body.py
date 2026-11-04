"""Export the NeuroMechFly body (Lobato-Rios et al. 2022; flygym, Apache-2.0) for the web viewer.
Body segments, their parent tree, their pose in NeuroMechFly's neutral standing pose, the mesh of each
segment in its own frame, and every joint axis. Lengths in mm."""
import json, warnings, numpy as np, mujoco
warnings.simplefilter('ignore')
from flygym.compose.fly.neuromechfly import NeuroMechFly
import flygym.anatomy as A
from flygym.compose.pose import KinematicPosePreset
fly = NeuroMechFly()
sk = A.Skeleton(axis_order=A.AxisOrder.YAW_PITCH_ROLL, joint_preset=A.JointPreset.ALL_BIOLOGICAL)
fly.add_joints(sk, neutral_pose=KinematicPosePreset.NEUTRAL)
m, d = fly.compile()
k = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_KEY, 'neutral')
if k >= 0: mujoco.mj_resetDataKeyframe(m, d, k)
mujoco.mj_forward(m, d)
name = lambda t, i: mujoco.mj_id2name(m, t, i)
def q2m(q): r = np.zeros(9); mujoco.mju_quat2Mat(r, q); return r.reshape(3, 3)
bodies, blobs, off = [], [], 0
for b in range(1, m.nbody):
    p = m.body_parentid[b]
    Rw, tw = d.xmat[b].reshape(3, 3), d.xpos[b]
    Rp, tp = (np.eye(3), np.zeros(3)) if p == 0 else (d.xmat[p].reshape(3, 3), d.xpos[p])
    Rl, tl = Rp.T @ Rw, Rp.T @ (tw - tp)
    ql = np.zeros(4); mujoco.mju_mat2Quat(ql, Rl.flatten())
    geoms = []
    for g in np.where(m.geom_bodyid == b)[0]:
        mid = m.geom_dataid[g]
        if m.geom_type[g] != mujoco.mjtGeom.mjGEOM_MESH or mid < 0: continue
        va, vn = m.mesh_vertadr[mid], m.mesh_vertnum[mid]; fa, fn = m.mesh_faceadr[mid], m.mesh_facenum[mid]
        V = m.mesh_vert[va:va + vn] @ q2m(m.geom_quat[g]).T + m.geom_pos[g]
        F = m.mesh_face[fa:fa + fn].astype(np.uint32)
        vb, fb = V.astype('<f4').tobytes(), F.astype('<u4').tobytes()
        geoms.append(dict(v=[int(off), int(vn)], f=[int(off + len(vb)), int(fn)])); blobs += [vb, fb]; off += len(vb) + len(fb)
    joints = [dict(name=name(mujoco.mjtObj.mjOBJ_JOINT, j), axis=[round(float(x), 5) for x in m.jnt_axis[j]], pos=[round(float(x), 5) for x in m.jnt_pos[j]])
              for j in np.where(m.jnt_bodyid == b)[0]]
    bodies.append(dict(name=name(mujoco.mjtObj.mjOBJ_BODY, b), parent=None if p == 0 else name(mujoco.mjtObj.mjOBJ_BODY, p),
                       pos=[round(float(x), 6) for x in tl], quat=[round(float(x), 6) for x in ql], geoms=geoms, joints=joints))
open('fly_body.bin', 'wb').write(b''.join(blobs))
json.dump(dict(source='NeuroMechFly (Lobato-Rios et al. 2022, Nature Methods; flygym 2.1.1, Apache-2.0), micro-CT-based body, simplified meshes, neutral pose; units mm; quaternions w,x,y,z',
               bodies=bodies), open('fly_body.json', 'w'), separators=(',', ':'))
print(len(bodies), 'bodies', off // 1024, 'KB', sum(len(b['joints']) for b in bodies), 'joints')
print([ (b['name'], [j['name'] for j in b['joints']]) for b in bodies if b['name'] in ('c_rostrum','c_haustellum','lf_coxa','lf_trochanterfemur','lf_tibia','l_pedicel','c_head')])
