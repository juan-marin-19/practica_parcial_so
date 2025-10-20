from pathlib import Path

# Clase que representa un proceso y almacena toda su información
class Process:
    def __init__(self, label, bt, at, q, pr):
        self.label = label           # Nombre o identificador del proceso
        self.bt = bt                 # Burst time
        self.at = at                 # Arrival tim
        self.q = q                   # Número de cola a la que pertenece (nivel del MLQ)
        self.pr = pr                 # Prioridad del proceso 
        self.remaining_bt = bt       # Tiempo restante por ejecutar
        self.wt = 0                  # Tiempo total de espera
        self.ct = 0                  # Completition time
        self.rt = -1                 # Tiempo de respuesta 
        self.tat = 0                 # Turnaround time 
        self.started = False         # Indica si el proceso ya empezó a ejecutarse


# Clase que implementa eL MLQ
class MLQScheduler:
    def __init__(self):
        # Tres colas de planificación, una por nivel del MLQ
        self.queues = [[], [], []]
        # Lista para guardar los procesos que ya terminaron
        self.finished_processes = []

    # Lee los procesos desde un archivo de texto
    def read_input(self, filename):
        with open(filename, 'r') as f:
            for line in f:
                # Ignora líneas vacías o comentarios
                if line.strip() and not line.strip().startswith('#'):
                    parts = [part.strip() for part in line.strip().split(';')]
                    label, bt, at, q, pr = parts

                    # Crea el proceso y lo agrega a su cola correspondiente
                    process = Process(label, int(bt), int(at), int(q) - 1, int(pr))
                    self.queues[process.q].append(process)

        # Ordena cada cola según el tiempo de llegada
        for q in self.queues:
            q.sort(key=lambda p: p.at)

    # Ejecuta la planificación MLQ (RR en las dos primeras colas, SJF en la tercera)
    def schedule(self):
        current_time = 0
        all_processes = [p for queue in self.queues for p in queue]

        # Corre mientras existan procesos sin finalizar
        while self.queues[0] or self.queues[1] or self.queues[2]:
            next_process = None

            # Cola 1, Round Robin con quantum = 1
            if self.queues[0]:
                ready_processes = [p for p in self.queues[0] if p.at <= current_time]
                if ready_processes:
                    next_process = ready_processes[0]

            # Cola 2, Round Robin con quantum = 3
            if not next_process and self.queues[1]:
                ready_processes = [p for p in self.queues[1] if p.at <= current_time]
                if ready_processes:
                    next_process = ready_processes[0]

            # Cola 3, SJF 
            if not next_process and self.queues[2]:
                ready_processes = [p for p in self.queues[2] if p.at <= current_time]
                if ready_processes:
                    # Ordenamos la lista de procesos segun el burst time restante de cada proceso 
                    ready_processes.sort(key=lambda p: p.remaining_bt)
                    next_process = ready_processes[0]

            # Si hay un proceso listo, se ejecuta según su tipo de cola
            if next_process:
                # Round Robin (para las colas 1 y 2)
                if next_process.q in [0, 1]:
                    quantum = 1 if next_process.q == 0 else 3

                    # Si es la primera vez que entra al CPU, se calcula su RT
                    if not next_process.started:
                        next_process.rt = current_time - next_process.at
                        next_process.started = True

                    # Ejecuta el proceso según el quantum o el tiempo restante
                    execute_time = min(quantum, next_process.remaining_bt)
                    next_process.remaining_bt -= execute_time
                    current_time += execute_time

                    # Si termina, se calculan sus métricas finales
                    if next_process.remaining_bt == 0:
                        next_process.ct = current_time
                        next_process.tat = next_process.ct - next_process.at
                        next_process.wt = next_process.tat - next_process.bt
                        self.queues[next_process.q].remove(next_process)
                        self.finished_processes.append(next_process)
                    # Si no termina, vuelve al final de su cola
                    else:
                        self.queues[next_process.q].remove(next_process)
                        self.queues[next_process.q].append(next_process)

                # SJF (cola 3)
                elif next_process.q == 2:
                    if not next_process.started:
                        next_process.rt = current_time - next_process.at
                        next_process.started = True

                    execute_time = next_process.remaining_bt
                    next_process.remaining_bt = 0
                    current_time += execute_time

                    next_process.ct = current_time
                    next_process.tat = next_process.ct - next_process.at
                    next_process.wt = next_process.tat - next_process.bt
                    self.queues[next_process.q].remove(next_process)
                    self.finished_processes.append(next_process)

            # Si no hay procesos listos, el tiempo avanza al siguiente proceso listo
            else:
                next_arrival_time = min([p.at for p in all_processes if p not in self.finished_processes])
                if next_arrival_time > current_time:
                    current_time = next_arrival_time

    # Genera el archivo de salida con los resultados del planificador
    def write_output(self, filename):
        # Ordena los procesos por su etiqueta (A, B, C, ...)
        self.finished_processes.sort(key=lambda x: x.label)

        with open(filename, 'w') as f:
            f.write(f"# archivo: {filename}\n")
            f.write("# etiqueta; BT; AT; Q; Pr; WT; CT; RT; TAT\n")

            # Escribe los datos de cada proceso
            for p in self.finished_processes:
                f.write(f"{p.label};{p.bt};{p.at};{p.q + 1};{p.pr};{p.wt};{p.ct};{p.rt};{p.tat}\n")

            # Calcula los promedios globales
            if self.finished_processes:
                avg_wt = sum(p.wt for p in self.finished_processes) / len(self.finished_processes)
                avg_ct = sum(p.ct for p in self.finished_processes) / len(self.finished_processes)
                avg_rt = sum(p.rt for p in self.finished_processes) / len(self.finished_processes)
                avg_tat = sum(p.tat for p in self.finished_processes) / len(self.finished_processes)
                f.write(f"\nWT={avg_wt}; CT={avg_ct}; RT={avg_rt}; TAT={avg_tat};\n")
            else:
                f.write("\nWT=0; CT=0; RT=0; TAT=0;\n")

# Ejecución de la simulación del MLQ
script_dir = Path(__file__).resolve().parent
file_path = script_dir / 'mlq019.txt'

scheduler = MLQScheduler()
scheduler.read_input(file_path)
scheduler.schedule()
scheduler.write_output(script_dir / 'mlq019_output.txt')



