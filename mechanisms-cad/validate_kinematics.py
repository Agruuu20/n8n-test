import numpy as np

def fourbar(theta1_deg, L1=5, L2=30, L3=60, D=(35,0), branch=1):
    A = np.array([0.0,0.0])
    D = np.array(D, dtype=float)
    t1 = np.radians(theta1_deg)
    B = A + L1*np.array([np.cos(t1), np.sin(t1)])
    d = D - B
    dist = np.linalg.norm(d)
    a = (L2**2 - L3**2 + dist**2) / (2*dist)
    h2 = L2**2 - a**2
    h = np.sqrt(max(h2,0))
    P = B + a*d/dist
    perp = np.array([-d[1], d[0]])/dist
    C1 = P + h*perp
    C2 = P - h*perp
    C = C1 if branch==1 else C2
    theta2 = np.degrees(np.arctan2(C[1]-B[1], C[0]-B[0])) % 360
    theta3 = np.degrees(np.arctan2(C[1]-D[1], C[0]-D[0])) % 360
    return B, C, theta2, theta3

table = {
 0:(180.00,180.00),
 45:(146.91,160.62),
 90:(124.99,150.46),
 135:(115.95,149.44),
 180:(117.28,153.62),
}
print("FOUR-BAR")
for th1, (t2ref,t3ref) in table.items():
    for branch in (1,2):
        B,C,t2,t3 = fourbar(th1, branch=branch)
        if abs(((t2-t2ref+180)%360)-180) < 1 and abs(((t3-t3ref+180)%360)-180) < 1:
            print(f"theta1={th1:>4} branch={branch}  theta2={t2:7.2f} (ref {t2ref})  theta3={t3:7.2f} (ref {t3ref})  B={B.round(3)} C={C.round(3)}")

def inv_slider_crank(theta1_deg, L1=80, L3=50, A=(0,0), C=(50,0)):
    A = np.array(A, dtype=float)
    Cf = np.array(C, dtype=float)
    t1 = np.radians(theta1_deg)
    B = A + L1*np.array([np.cos(t1), np.sin(t1)])
    CB = B - Cf
    Lcb = np.linalg.norm(CB)
    theta2 = np.degrees(np.arctan2(CB[1], CB[0])) % 360
    return B, Lcb, theta2

table2 = {
 0:(30.000,0.00),
 45:(56.949,83.38),
 90:(94.340,122.01),
 135:(120.652,152.04),
 180:(130.000,180.00),
}
print("\nINVERTED SLIDER-CRANK")
for th1, (lref,t2ref) in table2.items():
    B, Lcb, t2 = inv_slider_crank(th1)
    print(f"theta1={th1:>4}  Lcb={Lcb:8.3f} (ref {lref})  theta2={t2:7.2f} (ref {t2ref})  B={B.round(3)}")
