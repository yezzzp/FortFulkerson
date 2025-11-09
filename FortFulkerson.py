import tkinter as tk
from tkinter import ttk, messagebox
import math
import random
from collections import deque

ANCHO_VENTANA = 1020
ALTO_VENTANA = 640
ANCHO_CANVAS = 680
ALTO_CANVAS = 560
N_MIN, N_MAX = 8, 16
RADIO_NODO = 18
PROB_ARISTA = 0.25
CAP_MIN, CAP_MAX = 3, 15


class AplicacionFlujoMaximo(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Algoritmo de Flujo Máximo (Ford-Fulkerson)")
        self.geometry(f"{ANCHO_VENTANA}x{ALTO_VENTANA}")
        self.resizable(False, False)

        # Variables del programa
        self.num_nodos = tk.IntVar(value=8)
        self.modo = tk.StringVar(value="Automático")
        self.nodo_fuente = tk.StringVar()
        self.nodo_sumidero = tk.StringVar()

        # Estructuras
        self.posiciones = {}
        self.items_nodo = {}
        self.items_arista = {}
        self.capacidades = []
        self.flujo = []
        self.ocultar_flujo_cero = False

        self.crear_interfaz()

    # ------------- UI -------------
    def crear_interfaz(self):
        barra = ttk.Frame(self, padding=8)
        barra.pack(fill="x")

        ttk.Label(barra, text="Cantidad de nodos (8–16):").pack(side="left")
        ttk.Spinbox(barra, from_=N_MIN, to=N_MAX, textvariable=self.num_nodos, width=5)\
            .pack(side="left", padx=(4, 12))

        ttk.Label(barra, text="Modo:").pack(side="left")
        ttk.Combobox(barra, values=["Automático", "Manual"], textvariable=self.modo,
                     state="readonly", width=10).pack(side="left", padx=(4, 12))

        ttk.Button(barra, text="Generar grafo", command=self.generar_grafo)\
            .pack(side="left", padx=(4, 12))

        ttk.Separator(barra, orient="vertical").pack(
            side="left", fill="y", padx=10)

        ttk.Label(barra, text="Fuente:").pack(side="left")
        self.combo_fuente = ttk.Combobox(barra, width=6, state="readonly")
        self.combo_fuente.pack(side="left", padx=(4, 12))
        ttk.Label(barra, text="Sumidero:").pack(side="left")
        self.combo_sumidero = ttk.Combobox(barra, width=6, state="readonly")
        self.combo_sumidero.pack(side="left", padx=(4, 12))

        self.boton_ejecutar = ttk.Button(
            barra, text="Ejecutar algoritmo", command=self.ejecutar_algoritmo, state="disabled")
        self.boton_ejecutar.pack(side="left")

        # ----- Cuerpo central -----
        cuerpo = ttk.Frame(self, padding=(8, 0, 8, 8))
        cuerpo.pack(fill="both", expand=True)

        # Lado izquierdo
        izquierda = ttk.Frame(cuerpo)
        izquierda.pack(side="left", padx=(0, 10))
        self.lienzo = tk.Canvas(
            izquierda, width=ANCHO_CANVAS, height=ALTO_CANVAS,
            bg="white", highlightthickness=1, highlightbackground="#c8c8c8"
        )
        self.lienzo.pack()
        
        # Frame inferior para etiqueta y botón
        frame_inferior = ttk.Frame(izquierda)
        frame_inferior.pack(pady=(6, 0), fill="x")
        ttk.Label(frame_inferior, text="Grafo dirigido con capacidades").pack(side="left")
        self.boton_ocultar = ttk.Button(
            frame_inferior, text="Ocultar flujo 0", 
            command=self.toggle_flujo_cero, state="disabled"
        )
        self.boton_ocultar.pack(side="right", padx=(10, 0))

        # Lado derecho
        derecha = ttk.Frame(cuerpo)
        derecha.pack(side="left", fill="y")

        ttk.Label(derecha, text="Proceso paso a paso:", font=("Segoe UI", 10, "bold"))\
            .pack(anchor="w")
        self.caja_proceso = tk.Text(
            derecha, width=45, height=28, font=("Consolas", 10))
        self.caja_proceso.pack(pady=(2, 8))

        # ---- Panel Modo Manual ----
        self.panel_manual = ttk.LabelFrame(
            derecha, text="Arista manual (u -> v, capacidad)")
        self.panel_manual.pack(fill="x", pady=(0, 8))

        ttk.Label(self.panel_manual, text="Nodo u:").grid(
            row=0, column=0, padx=4, pady=4)
        ttk.Label(self.panel_manual, text="Nodo v:").grid(
            row=0, column=1, padx=4, pady=4)
        ttk.Label(self.panel_manual, text="Capacidad:").grid(
            row=0, column=2, padx=4, pady=4)

        self.ent_u = ttk.Entry(self.panel_manual, width=5)
        self.ent_v = ttk.Entry(self.panel_manual, width=5)
        self.ent_capacidad = ttk.Entry(self.panel_manual, width=7)
        self.ent_u.grid(row=1, column=0, padx=4, pady=4)
        self.ent_v.grid(row=1, column=1, padx=4, pady=4)
        self.ent_capacidad.grid(row=1, column=2, padx=4, pady=4)

        ttk.Button(self.panel_manual, text="Agregar/Actualizar",
                   command=self.agregar_arista_desde_formulario).grid(row=1, column=3, padx=6)
        # Aquí enlazamos al limpiador general (no a una función inexistente)
        ttk.Button(self.panel_manual, text="Limpiar aristas",
                   command=self.limpiar_aristas).grid(row=1, column=4, padx=6)

        # Pie de ventana
        pie = ttk.Frame(self, padding=(8, 0, 8, 8))
        pie.pack(fill="x")
        self.etiqueta_estado = ttk.Label(pie, text="Listo.")
        self.etiqueta_estado.pack(anchor="w")

    # --- Función de generación de grafo ---
    def generar_grafo(self):
        n = max(N_MIN, min(N_MAX, self.num_nodos.get()))
        self.num_nodos.set(n)
        self.lienzo.delete("all")
        self.caja_proceso.delete("1.0", "end")
        self.items_nodo.clear()
        self.items_arista.clear()
        self.posiciones = self.calcular_posiciones(n)

        # --- Inicializar matriz de capacidades ---
        self.capacidades = [[0]*n for _ in range(n)]
        self.flujo = [[0]*n for _ in range(n)]

        # --- Generar aristas si es Automático ---
        if self.modo.get() == "Automático":
            for u in range(n):
                for v in range(n):
                    if u != v and random.random() < PROB_ARISTA:
                        if self.capacidades[u][v] == 0 and self.capacidades[v][u] == 0:
                            capacidad = random.randint(CAP_MIN, CAP_MAX)
                            self.capacidades[u][v] = capacidad
                            self.dibujar_arista(u, v, capacidad)
            self.panel_manual.state(["disabled"])
        else:
            self.panel_manual.state(["!disabled"])
        self.dibujar_nodos(n)

        # Fuente y sumidero
        valores = [str(i+1) for i in range(n)]
        self.combo_fuente.config(values=valores)
        self.combo_sumidero.config(values=valores)
        self.combo_fuente.set("1")
        self.combo_sumidero.set("2")
        self.boton_ejecutar.config(state="normal")
        self.boton_ocultar.config(state="disabled")
        self.ocultar_flujo_cero = False

        self.caja_proceso.insert("end", f"Grafo generado con {n} nodos.\n")
        self.etiqueta_estado.config(
            text="Listo para agregar aristas o ejecutar.")

    def calcular_posiciones(self, n):
        cx, cy = ANCHO_CANVAS // 2, ALTO_CANVAS // 2
        R = min(ANCHO_CANVAS, ALTO_CANVAS) // 2 - 70
        pos = {}
        for i in range(n):
            ang = 2*math.pi*i/n - math.pi/2
            pos[i] = (cx + R*math.cos(ang), cy + R*math.sin(ang))
        return pos

    def dibujar_nodos(self, n):
        for i in range(n):
            x, y = self.posiciones[i]
            id_ovalo = self.lienzo.create_oval(
                x - RADIO_NODO, y - RADIO_NODO,
                x + RADIO_NODO, y + RADIO_NODO,
                fill="#bfe3ff", outline="#2980b9", width=2)
            id_texto = self.lienzo.create_text(
                x, y, text=str(i + 1), font=("Segoe UI", 10, "bold"))
            self.items_nodo[i] = (id_ovalo, id_texto)

    # --- Aristas ---
    def punto_borde(self, x1, y1, x2, y2, radio):
        dx, dy = x2 - x1, y2 - y1
        dist = math.hypot(dx, dy)
        if dist == 0:
            return x2, y2
        ux, uy = dx / dist, dy / dist
        return x2 - ux * radio, y2 - uy * radio

    def dibujar_arista(self, u, v, capacidad):
        x1, y1 = self.posiciones[u]
        x2, y2 = self.posiciones[v]

        ox, oy = self.punto_borde(x2, y2, x1, y1, RADIO_NODO)
        dx, dy = self.punto_borde(x1, y1, x2, y2, RADIO_NODO + 2)

        linea = self.lienzo.create_line(
            ox, oy, dx, dy, arrow=tk.LAST, width=1.6)
        mx, my = (ox + dx) / 2, (oy + dy) / 2
        offx, offy = (dy - oy), -(dx - ox)
        norm = max(1, math.hypot(offx, offy))
        mx += 12 * offx / norm
        my += 12 * offy / norm
        valor = f"{self.flujo[u][v]}/{capacidad}"
        texto = self.lienzo.create_text(
            mx, my, text=valor, font=("Segoe UI", 9, ), fill="#2c3e50")
        self.items_arista[(u, v)] = (linea, texto)

    # --- Modo Manual ---
    def agregar_arista_desde_formulario(self):
        n = self.num_nodos.get()
        try:
            u = int(self.ent_u.get()) - 1
            v = int(self.ent_v.get()) - 1
            capacidad = int(self.ent_capacidad.get())
        except:
            messagebox.showerror(
                "Datos inválidos", "Ingrese U, V y capacidad como enteros.")
            return

        if not (0 <= u < n and 0 <= v < n) or u == v or capacidad <= 0:
            messagebox.showerror(
                "Datos inválidos", "Debe cumplirse: 1 <= U,V <= N, U != V, Capacidad > 0.")
            return

        if self.capacidades[v][u] > 0:
            messagebox.showerror(
                "Arista inválida", f"Ya existe una arista en sentido contrario ({v+1} -> {u+1}).")
            return

        self.capacidades[u][v] = capacidad
        if (u, v) in self.items_arista:
            _, txt = self.items_arista[(u, v)]
            self.lienzo.itemconfig(txt, text=f"{self.flujo[u][v]}/{capacidad}")
        else:
            self.dibujar_arista(u, v, capacidad)
            self.dibujar_nodos(n)
        self.actualizar_etiquetas_y_colores()
        self.caja_proceso.insert(
            "end", f"Arista: {u+1} -> {v+1} (capacidad {capacidad})\n")

    def limpiar_aristas(self):
        n = self.num_nodos.get()
        for (u, v), (linea, texto) in list(self.items_arista.items()):
            self.lienzo.delete(linea)
            self.lienzo.delete(texto)
        self.items_arista.clear()
        self.capacidades = [[0]*n for _ in range(n)]
        self.flujo = [[0]*n for _ in range(n)]
        self.dibujar_nodos(n)
        self.caja_proceso.insert(
            "end", "Todas las aristas han sido eliminadas.\n")

    # ------ Algoritmo Ford-Fulkerson ------
    def construir_residual(self):
        n = len(self.capacidades)
        R = [[0]*n for _ in range(n)]
        for u in range(n):
            for v in range(n):
                R[u][v] = self.capacidades[u][v] - self.flujo[u][v]
                R[v][u] += self.flujo[u][v]
        return R

    def bfs_residual(self, R, s, t):
        n = len(R)
        parent = [-1]*n
        parent[s] = s
        q = deque([s])
        while q:
            u = q.popleft()
            for v in range(n):
                if parent[v] == -1 and R[u][v] > 0:
                    parent[v] = u
                    if v == t:
                        cuello = float('inf')
                        x = t
                        while x != s:
                            cuello = min(cuello, R[parent[x]][x])
                            x = parent[x]
                        return parent, cuello
                    q.append(v)
        return None, 0

    def actualizar_etiquetas_y_colores(self):
        for (u, v), (linea, texto) in self.items_arista.items():
            f = self.flujo[u][v]
            c = self.capacidades[u][v]
            self.lienzo.itemconfig(texto, text=f"{f}/{c}")
            
            # Determinar si ocultar
            if self.ocultar_flujo_cero and f == 0:
                self.lienzo.itemconfig(linea, state="hidden")
                self.lienzo.itemconfig(texto, state="hidden")
            else:
                self.lienzo.itemconfig(linea, state="normal")
                self.lienzo.itemconfig(texto, state="normal")
                
                # Aplicar colores
                if c > 0 and f >= c:
                    self.lienzo.itemconfig(linea, fill="#e74c3c", width=2.2)
                    self.lienzo.itemconfig(texto, fill="#e74c3c")
                elif f > 0:
                    self.lienzo.itemconfig(linea, fill="#3142dc", width=1.8)
                    self.lienzo.itemconfig(texto, fill="#3142dc")
                else:
                    self.lienzo.itemconfig(linea, fill="#030303", width=1.8)
                    self.lienzo.itemconfig(texto, fill="#030303")

    def corte_minimo(self, R, s):
        n = len(R)
        visitado = [False]*n
        q = deque([s])
        visitado[s] = True
        while q:
            u = q.popleft()
            for v in range(n):
                if not visitado[v] and R[u][v] > 0:
                    visitado[v] = True
                    q.append(v)
        S = {i for i, ok in enumerate(visitado) if ok}
        T = {i for i in range(n) if i not in S}
        return S, T

    def toggle_flujo_cero(self):
        """Alterna entre ocultar y mostrar aristas con flujo cero"""
        self.ocultar_flujo_cero = not self.ocultar_flujo_cero
        
        if self.ocultar_flujo_cero:
            self.boton_ocultar.config(text="Mostrar flujo 0")
        else:
            self.boton_ocultar.config(text="Ocultar flujo 0")
        
        self.actualizar_etiquetas_y_colores()

    def ejecutar_algoritmo(self):
        try:
            s = int(self.combo_fuente.get()) - 1
            t = int(self.combo_sumidero.get()) - 1
        except:
            messagebox.showerror(
                "Datos inválidos", "Seleccione nodos fuente y sumidero válidos.")
            return
        if s == t:
            messagebox.showerror(
                "Datos inválidos", "El nodo fuente y sumidero deben ser diferentes.")
            return
        n = self.num_nodos.get()
        self.flujo = [[0]*n for _ in range(n)]
        self.actualizar_etiquetas_y_colores()
        self.caja_proceso.delete("1.0", "end")

        paso = 1
        maxflow = 0

        while True:
            R = self.construir_residual()
            parent, cuello = self.bfs_residual(R, s, t)
            if cuello == 0:
                break

            camino = []
            v = t
            while v != s:
                u = parent[v]
                camino.append((u, v))
                v = u
            camino.reverse()

            self.caja_proceso.insert("end", f"Paso {paso}: Camino ")
            self.caja_proceso.insert("end", " -> ".join(str(u+1)
                                     for (u, _) in camino) + f" -> {t+1}\n")
            self.caja_proceso.insert("end", f"  Cuello: {cuello}\n")

            for (u, v) in camino:
                if self.capacidades[u][v] > 0:
                    self.flujo[u][v] += cuello
                else:
                    self.flujo[v][u] -= cuello

            maxflow += cuello
            paso += 1
            self.actualizar_etiquetas_y_colores()
            self.update_idletasks()

        Rf = self.construir_residual()
        S, T = self.corte_minimo(Rf, s)

        for i in range(n):
            oval, _ = self.items_nodo[i]
            if i in S:
                self.lienzo.itemconfig(oval, fill="#d6f5d6")
            else:
                self.lienzo.itemconfig(oval, fill="#ffd9d9")

        cap_cut = sum(self.capacidades[u][v]
                      for u in S for v in T if self.capacidades[u][v] > 0)

        self.caja_proceso.insert(
            "end", "================ RESULTADOS ================\n")
        self.caja_proceso.insert("end", f"Flujo máximo: {maxflow}\n")
        self.caja_proceso.insert(
            "end", f"Capacidad del corte mínimo: {cap_cut}\n")
        self.caja_proceso.insert(
            "end", f"S = {{{', '.join(str(x+1) for x in sorted(S))}}}\n")
        self.caja_proceso.insert(
            "end", f"T = {{{', '.join(str(x+1) for x in sorted(T))}}}\n")
        
        # Habilitar el botón de ocultar flujo cero después de ejecutar
        self.boton_ocultar.config(state="normal")


# --- Ejecutar la aplicación ---
if __name__ == "__main__":
    app = AplicacionFlujoMaximo()
    app.mainloop()
