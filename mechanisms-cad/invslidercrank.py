"""Mecanismo de biela-manivela invertido (inverted slider-crank).

Datos del informe:
  A = (0,0)   pivote fijo de la manivela
  C = (50,0)  pivote fijo del eslabon-guia (ranurado)
  L1 = 80 mm  manivela (A->B)
  L3 = 50 mm  bancada (A->C)  [= distancia entre A y C]

theta1: angulo de la manivela. B = A + L1<theta1.
Lcb = |B - C| (posicion del bloque deslizante dentro de la ranura, medida
desde el pivote C). theta2 = angulo del eslabon-guia (direccion C->B).

Verificado contra la tabla teorica del informe (Lcb, theta2 en funcion de
theta1): coincide exactamente.

Rango fisico de Lcb a lo largo de una vuelta completa de la manivela:
  Lcb_min = |L1 - L3| = 30 mm   (theta1 = 0 deg)
  Lcb_max = L1 + L3   = 130 mm  (theta1 = 180 deg)
La ranura del eslabon-guia se dimensiona para cubrir ese rango completo, de
forma que el mecanismo generado sea funcional para cualquier theta1, no solo
para la posicion exportada.
"""
import math
import sys
import cadquery as cq
from common import bar_link, pin, guide_slot_link, slider_block

A = (0.0, 0.0)
C = (50.0, 0.0)
L1, L3 = 80.0, 50.0

LCB_MIN = abs(L1 - L3)
LCB_MAX = L1 + L3

GROUND_WIDTH = 10.0
CRANK_WIDTH = 9.0
THICK = 6.0
HOLE_D = 5.0
PIN_D = 4.6
PIN_MARGIN = 2.0

GUIDE_BODY_MARGIN = 12.0
GUIDE_BODY_START = 0.0
SLOT_MARGIN = 6.0
SLOT_WIDTH = 11.0
BLOCK_LEN = 14.0
BLOCK_WIDTH = 10.0


def solve(theta1_deg):
    t1 = math.radians(theta1_deg)
    B = (A[0] + L1 * math.cos(t1), A[1] + L1 * math.sin(t1))
    cbx, cby = B[0] - C[0], B[1] - C[1]
    Lcb = math.hypot(cbx, cby)
    theta2 = math.degrees(math.atan2(cby, cbx)) % 360
    return B, Lcb, theta2


def build_assembly(theta1_deg):
    B, Lcb, theta2 = solve(theta1_deg)

    ground = bar_link(A, C, GROUND_WIDTH, THICK, HOLE_D)
    crank = bar_link(A, B, CRANK_WIDTH, THICK, HOLE_D)

    guide = guide_slot_link(
        pivot_xy=C, angle_deg=theta2,
        u_body_start=GUIDE_BODY_START, u_body_end=LCB_MAX + GUIDE_BODY_MARGIN,
        u_slot_start=LCB_MIN - SLOT_MARGIN, u_slot_end=LCB_MAX + SLOT_MARGIN,
        body_width=SLOT_WIDTH + 2 * 3.0, slot_width=SLOT_WIDTH,
        thickness=THICK, pivot_hole_d=HOLE_D,
    )
    block = slider_block(
        pivot_xy=C, angle_deg=theta2, u_center=Lcb,
        block_len=BLOCK_LEN, block_width=BLOCK_WIDTH,
        thickness=THICK, hole_d=HOLE_D,
    )

    z0, z1 = -PIN_MARGIN, THICK + PIN_MARGIN
    pin_A = pin(A, PIN_D, z0, z1)
    pin_C = pin(C, PIN_D, z0, z1)
    pin_B = pin(B, PIN_D, z0, z1)

    assy = cq.Assembly(name=f"BielaManivelaInvertido_theta1_{theta1_deg:g}deg")
    assy.add(ground, name="Bancada_AC", color=cq.Color(0.55, 0.55, 0.58))
    assy.add(crank, name="L1_Manivela", color=cq.Color(0.85, 0.2, 0.2))
    assy.add(guide, name="Eslabon_Guia_Ranurado", color=cq.Color(0.2, 0.35, 0.85))
    assy.add(block, name="Bloque_Deslizante", color=cq.Color(0.2, 0.65, 0.25))
    assy.add(pin_A, name="Pasador_A", color=cq.Color(0.9, 0.75, 0.1))
    assy.add(pin_B, name="Pasador_B", color=cq.Color(0.9, 0.75, 0.1))
    assy.add(pin_C, name="Pasador_C", color=cq.Color(0.9, 0.75, 0.1))
    return assy, (B, Lcb, theta2)


if __name__ == "__main__":
    theta1 = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
    outbase = sys.argv[2] if len(sys.argv) > 2 else f"invslidercrank_theta1_{theta1:g}"

    assy, (B, Lcb, theta2) = build_assembly(theta1)
    print(f"theta1={theta1}  B={B}  Lcb={Lcb:.3f}  theta2={theta2:.2f}")

    assy.save(f"{outbase}.step")
    assy.save(f"{outbase}.stl")
