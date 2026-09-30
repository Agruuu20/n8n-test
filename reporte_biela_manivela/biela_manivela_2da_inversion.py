"""Analisis cinematico del mecanismo biela-manivela (2da inversion).

A = (0,0) pivote de la manivela (L1), C = (L3,0) pivote de la guia.
theta_3 = 180 deg  ->  R1 + R3 = R2
Incognitas: L2 (distancia C-B) y theta_2 (angulo de la guia CB).
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def pedir(texto, defecto):
    """Pide un dato al usuario; Enter = valor por defecto."""
    r = input(f"{texto} [{defecto}]: ").strip()
    return float(r) if r else float(defecto)


# ---------------- Posicion (Newton-Raphson) ----------------
def posicion(th1, L1, L3, x0):
    """Resuelve F(L2,th2)=0 con Newton-Raphson. x0 = (L2, th2) inicial."""
    x = np.array(x0, dtype=float)
    for _ in range(100):
        L2, th2 = x
        F = np.array([L1*np.sin(th1) - L2*np.sin(th2),
                      L1*np.cos(th1) - L3 - L2*np.cos(th2)])
        J = np.array([[-np.sin(th2), -L2*np.cos(th2)],
                      [-np.cos(th2),  L2*np.sin(th2)]])
        dx = np.linalg.solve(J, F)
        x = x - dx
        if np.linalg.norm(dx) < 1e-10:
            break
    if x[0] < 0:                      # rama fisica L2 > 0
        x = np.array([-x[0], x[1] + np.pi])
    return x


# ---------------- Velocidad y aceleracion ----------------
def velocidad(th1, w1, L1, L2, th2):
    """Resuelve [L2dot, w2] de las ecuaciones de velocidad."""
    M = np.array([[np.sin(th2),  L2*np.cos(th2)],
                  [np.cos(th2), -L2*np.sin(th2)]])
    b = np.array([L1*w1*np.cos(th1), -L1*w1*np.sin(th1)])
    return np.linalg.solve(M, b)


def aceleracion(th1, w1, a1, L1, L2, th2, L2d, w2):
    """Resuelve [L2ddot, alpha2] de las ecuaciones de aceleracion."""
    M = np.array([[np.sin(th2),  L2*np.cos(th2)],
                  [np.cos(th2), -L2*np.sin(th2)]])
    b = np.array([
        L1*(a1*np.cos(th1) - w1**2*np.sin(th1))
        - 2*L2d*w2*np.cos(th2) + L2*w2**2*np.sin(th2),
        -L1*(a1*np.sin(th1) + w1**2*np.cos(th1))
        + 2*L2d*w2*np.sin(th2) + L2*w2**2*np.cos(th2)])
    return np.linalg.solve(M, b)


def simular(L1, L3, w1, th10, T, dt, a1=0.0):
    t = np.arange(0, T + dt/2, dt)
    th1 = th10 + w1*t + 0.5*a1*t**2
    w1t = w1 + a1*t
    n = len(t)
    R = {k: np.zeros(n) for k in
         ["L2", "th2", "L2d", "w2", "L2dd", "a2", "vBx", "vBy", "aBx", "aBy"]}
    for i in range(n):
        Bx, By = L1*np.cos(th1[i]), L1*np.sin(th1[i])
        x0 = (np.hypot(Bx - L3, By), np.arctan2(By, Bx - L3))   # estimado inicial
        L2, th2 = posicion(th1[i], L1, L3, x0)
        L2d, w2 = velocidad(th1[i], w1t[i], L1, L2, th2)
        L2dd, a2 = aceleracion(th1[i], w1t[i], a1, L1, L2, th2, L2d, w2)
        R["L2"][i], R["th2"][i] = L2, th2
        R["L2d"][i], R["w2"][i] = L2d, w2
        R["L2dd"][i], R["a2"][i] = L2dd, a2
        # punto B (manivela): v = w x r, a = alpha x r - w^2 r
        R["vBx"][i], R["vBy"][i] = -L1*w1t[i]*np.sin(th1[i]), L1*w1t[i]*np.cos(th1[i])
        R["aBx"][i] = -L1*(a1*np.sin(th1[i]) + w1t[i]**2*np.cos(th1[i]))
        R["aBy"][i] = L1*(a1*np.cos(th1[i]) - w1t[i]**2*np.sin(th1[i]))
    R["t"], R["th1"] = t, th1
    return R


def leer_csv(ruta):
    filas = list(csv.reader(open(ruta, encoding="latin1")))[2:]
    return np.array([[float(x) for x in f] for f in filas if f])


def graficar(R, prefijo="resultado"):
    t = R["t"]
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(t, R["L2"], label="L2 (mm)")
    ax[0].set_ylabel("mm"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(t, np.degrees(R["th2"]) % 360, "tab:red", label="theta2 (deg)")
    ax[1].set_ylabel("grados"); ax[1].set_xlabel("t (s)"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Posicion del deslizador y de la guia CB"); fig.tight_layout()
    fig.savefig(f"{prefijo}_pos.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(t, R["L2d"], label="dL2/dt (mm/s)")
    ax[0].set_ylabel("mm/s"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(t, R["w2"], "tab:red", label="w2 (rad/s)")
    ax[1].set_ylabel("rad/s"); ax[1].set_xlabel("t (s)"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Velocidades de la guia CB y del deslizador"); fig.tight_layout()
    fig.savefig(f"{prefijo}_vel.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax[0].plot(t, R["L2dd"], label="d2L2/dt2 (mm/s2)")
    ax[0].set_ylabel("mm/s2"); ax[0].legend(); ax[0].grid(alpha=.3)
    ax[1].plot(t, R["a2"], "tab:red", label="alpha2 (rad/s2)")
    ax[1].set_ylabel("rad/s2"); ax[1].set_xlabel("t (s)"); ax[1].legend(); ax[1].grid(alpha=.3)
    fig.suptitle("Aceleraciones de la guia CB y del deslizador"); fig.tight_layout()
    fig.savefig(f"{prefijo}_acc.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    print("Biela-manivela (2da inversion) - A=(0,0), C=(L3,0)")
    L1 = pedir("L1 manivela AB (mm)", 100)
    L3 = pedir("L3 distancia AC (mm)", 132.88)
    rpm = pedir("Velocidad de la manivela (rpm, + antihorario)", 100)
    th10 = np.radians(pedir("Angulo inicial theta1 (deg)", 138))
    T = pedir("Tiempo de simulacion (s)", 5)
    dt = pedir("Paso de tiempo (s)", 0.01)
    if abs(L1 - L3) < 1e-9:
        print("Aviso: L1 = L3, hay una singularidad (L2 = 0) cuando B coincide con C.")
    w1 = rpm*2*np.pi/60
    R = simular(L1, L3, w1, th10, T, dt)
    graficar(R)
    print(f"max|dL2/dt|={abs(R['L2d']).max():.2f} mm/s  max|w2|={abs(R['w2']).max():.3f} rad/s")
    print(f"max|L2dd|={abs(R['L2dd']).max():.1f} mm/s2  max|a2|={abs(R['a2']).max():.2f} rad/s2")
    # Comparacion opcional con SolidWorks
    rv = input("CSV de velocidad de SolidWorks (Enter para omitir): ").strip()
    ra = input("CSV de aceleracion de SolidWorks (Enter para omitir): ").strip()
    if rv and ra:
        V, A = leer_csv(rv), leer_csv(ra)
        print("Error max vx:", abs(R["vBx"][:len(V)] - V[:, 1]).max(), "mm/s")
        print("Error max ax:", abs(R["aBx"][:len(A)] - A[:, 1]).max(), "mm/s2")
