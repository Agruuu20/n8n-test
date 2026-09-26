"""Mecanismo de cuatro barras.

Datos del informe:
  L1 = 5 mm  (manivela, pivote fijo A = (0,0))
  L2 = 30 mm (acoplador, B->C)
  L3 = 60 mm (balancin, D->C)
  L4 = 35 mm (bancada, A->D), Delta X = 35, Delta Y = 0  =>  D = (35, 0)

Convencion verificada contra la tabla teorica (theta2, theta3 en funcion de
theta1) del informe: B = A + L1<theta1 ; C = B + L2<theta2 = D + L3<theta3.
Se resuelve el lazo vectorial (interseccion de dos circunferencias) tomando
la rama que reproduce exactamente los valores tabulados.
"""
import math
import sys
import cadquery as cq
from common import bar_link, pin

A = (0.0, 0.0)
D = (35.0, 0.0)
L1, L2, L3, L4 = 5.0, 30.0, 60.0, 35.0

WIDTH = 4.0
THICK = 3.0
HOLE_D = 2.0
PIN_D = 1.8
PIN_MARGIN = 1.5


def solve(theta1_deg, branch=1):
    t1 = math.radians(theta1_deg)
    B = (A[0] + L1 * math.cos(t1), A[1] + L1 * math.sin(t1))
    dx, dy = D[0] - B[0], D[1] - B[1]
    dist = math.hypot(dx, dy)
    a = (L2 ** 2 - L3 ** 2 + dist ** 2) / (2 * dist)
    h = math.sqrt(max(L2 ** 2 - a ** 2, 0.0))
    px, py = B[0] + a * dx / dist, B[1] + a * dy / dist
    perp = (-dy / dist, dx / dist)
    if branch == 1:
        C = (px + h * perp[0], py + h * perp[1])
    else:
        C = (px - h * perp[0], py - h * perp[1])
    theta2 = math.degrees(math.atan2(C[1] - B[1], C[0] - B[0])) % 360
    theta3 = math.degrees(math.atan2(C[1] - D[1], C[0] - D[0])) % 360
    return B, C, theta2, theta3


def build_assembly(theta1_deg):
    B, C, theta2, theta3 = solve(theta1_deg)

    ground = bar_link(A, D, WIDTH, THICK, HOLE_D)
    crank = bar_link(A, B, WIDTH, THICK, HOLE_D)
    coupler = bar_link(B, C, WIDTH, THICK, HOLE_D)
    rocker = bar_link(D, C, WIDTH, THICK, HOLE_D)

    z0, z1 = -PIN_MARGIN, THICK + PIN_MARGIN
    pin_A = pin(A, PIN_D, z0, z1)
    pin_B = pin(B, PIN_D, z0, z1)
    pin_C = pin(C, PIN_D, z0, z1)
    pin_D = pin(D, PIN_D, z0, z1)

    assy = cq.Assembly(name=f"CuatroBarras_theta1_{theta1_deg:g}deg")
    assy.add(ground, name="L4_Bancada", color=cq.Color(0.55, 0.55, 0.58))
    assy.add(crank, name="L1_Manivela", color=cq.Color(0.85, 0.2, 0.2))
    assy.add(coupler, name="L2_Acoplador", color=cq.Color(0.2, 0.65, 0.25))
    assy.add(rocker, name="L3_Balancin", color=cq.Color(0.2, 0.35, 0.85))
    assy.add(pin_A, name="Pasador_A", color=cq.Color(0.9, 0.75, 0.1))
    assy.add(pin_B, name="Pasador_B", color=cq.Color(0.9, 0.75, 0.1))
    assy.add(pin_C, name="Pasador_C", color=cq.Color(0.9, 0.75, 0.1))
    assy.add(pin_D, name="Pasador_D", color=cq.Color(0.9, 0.75, 0.1))
    return assy, (B, C, theta2, theta3)


if __name__ == "__main__":
    theta1 = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    outbase = sys.argv[2] if len(sys.argv) > 2 else f"fourbar_theta1_{theta1:g}"

    assy, (B, C, theta2, theta3) = build_assembly(theta1)
    print(f"theta1={theta1}  B={B}  C={C}  theta2={theta2:.2f}  theta3={theta3:.2f}")

    assy.save(f"{outbase}.step")
    assy.save(f"{outbase}.stl")
