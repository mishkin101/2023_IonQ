# import packages
from qiskit import QuantumCircuit, transpile
from qiskit.visualization import plot_histogram
from qiskit_ionq import IonQProvider
from playsound import *
from random import randint, random
from numpy import pi
from numpy.random import choice
provider = IonQProvider(token='1oyMIFGGrziz9w5PtiTVeqPEtOKUGYoe')

class Composer:
    SGL_GATES = ('X','Y','Z','H')
    SGL_GATES_PARAM = ('RX', 'RY', 'RZ')
    TWO_GATES = ('CX', 'CZ')
    
    def __init__(self, n, name):
        self.notes_circuits = []
        self.circ = None
        self.num_qubits = n
        self.name = name
        self.new_note()
        self.final_meas = []
        
    """ Circuit creation """    
    
    def new_note(self):
        self.notes_circuits.append(
            QuantumCircuit(self.num_qubits,self.num_qubits)
        )
        self.circ = self.notes_circuits[-1]
        
        
    # gates = ['X','Y','Z','H']
    def add_single_qubit_gate(self, gate, idx):
        gate = gate.upper()
        if gate not in self.SGL_GATES:
            raise Exception('invalid gate')
        if gate == 'X':
            self.circ.x(idx)
        elif gate == 'Y':
            self.circ.y(idx)
        elif gate == 'Z':
            self.circ.z(idx)
        elif gate == 'H':
            self.circ.h(idx)
        return
    
    # gates = ['RX', 'RY', 'RZ']
    def add_single_qubit_gate_wparam(self, gate, idx, param):
        gate = gate.upper()
        if gate not in self.SGL_GATES_PARAM:
            raise Exception('invalid gate')
        if gate == 'RX':
            self.circ.rx(param, idx)
        elif gate == 'RY':
            self.circ.ry(param, idx)
        elif gate == 'RZ':
            self.circ.rz(param, idx)

    # gate == ['CX', 'CZ']
    def add_two_qubit_gate(self, gate, idx_src, idx_dst):
        gate = gate.upper()
        if gate not in self.TWO_GATES:
            raise Exception('invalid gate')
        if gate == 'CX':
            self.circ.cx(idx_src, idx_dst)
        elif gate == 'CZ':
            self.circ.cz(idx_src, idx_dst)
            
    
    """ Generating the music """
    
    def run_job(self):
        # sends the circuits to hardware/simulator, waits and retrieves results
        # returns a formatted-results file

        final_meas = []
        init_state = randint(0, pow(2, self.num_qubits)-1)
        for cir in self.notes_circuits:

            print('initial', init_state)
            circuit = QuantumCircuit(self.num_qubits, self.num_qubits)

            circuit.prepare_state(init_state, circuit.qubits)
            circuit = circuit.compose(cir)

            circuit.measure(range(self.num_qubits), range(self.num_qubits))
            backend = provider.get_backend("ionq_simulator")
            transpiled = transpile(circuit, backend)

            job = backend.run(transpiled, shots=1)
            result = job.result()

            counts = result.get_counts()
            print('counts', counts)

            init_state = list(counts.keys())[list(counts.values()).index(1)]
            final_meas.append(init_state)
        self.final_meas = final_meas
    
    def generate_audio(self):
        # creates audio file from note sequence
        print('self.final_meas', self.final_meas)
        play_notes(write_to_midi(self.final_meas))

    
    def compose(self):
        results = self.run_job()
        notes = self.map_to_notes(results)
        return self.generate_audio(notes)
    
    
    """ Display """
    
    def dump(self):
        print("BEGIN COMPOSER")        
        for i, circ in enumerate(self.notes_circuits):
            print ("="*50)
            print(f"\t\tNote {i+1}")
            print(circ.draw())
        print("="*50)
        print("END COMPOSER")
        
        
class Sandbox_CLI:
    HELP = 'HELP'
    NEW = 'NEW'
    END = 'END'
    VIEWCURRENT = 'VIEW'
    VIEWALL = 'VIEWALL'
    
    def __init__(self):
        self.current_composer = None
        self.num_qubits = 8
        self.composers = dict()

    
    def init_composer(self, name):
        self.current_composer = Composer(self.num_qubits, name)
        self.composers[name] = self.current_composer     
    
        
    def construct_composer(self):
        while (True):
            uin = input('> ').upper()
            tokens = uin.split()
            cmd = tokens[0]
            if cmd == self.HELP:
                self.do_help()
            elif cmd == self.NEW:
                self.do_new()
            elif cmd == self.END:
                self.do_end()
                break
            elif cmd == self.VIEWALL:
                self.current_composer.dump()
            elif cmd in self.current_composer.SGL_GATES:
                self.do_sgl(tokens)
            elif cmd in self.current_composer.SGL_GATES_PARAM:
                self.do_sgl_param(tokens)
            elif cmd in self.current_composer.TWO_GATES:
                self.do_two(tokens)
            else:
                self.do_error()
        print("Circuit done")
        return

    def construct_composer_auto(self):
        while (True):
            uin = input('> ').upper()
            tokens = uin.split()
            cmd = tokens[0]
            if cmd == self.HELP:
                self.do_help()
            elif cmd == self.NEW:
                print("Disabled in AUTO mode.")
            elif cmd == self.END:
                break
            elif cmd == self.VIEWALL:
                self.current_composer.dump()
            elif cmd in self.current_composer.SGL_GATES:
                self.do_sgl(tokens)
            elif cmd in self.current_composer.SGL_GATES_PARAM:
                self.do_sgl_param(tokens)
            elif cmd in self.current_composer.TWO_GATES:
                self.do_two(tokens)
            else:
                self.do_error()
        print("Circuit Done")

        master_circuit = self.current_composer.notes_circuits[0]
        while len(master_circuit.data) > 1:
            master_circuit = master_circuit.copy()
            master_circuit.data.pop()
            self.current_composer.notes_circuits.insert(0, master_circuit)
    
        return
    
    def construct_composer_random(self, num_notes):
        # generate a random sequence of instructions
        n = self.current_composer.num_qubits
        commands = []
        for i in range(num_notes):
            remaining = 100
            while True:
                commands.append(self.random_command(n))
                r = random()
                if r < 0.1 or remaining == 0:
                    break
                remaining -= 1
            commands.append(['new'])
        
        commands[-1]= ['end']

        for tokens in commands:
            cmd = tokens[0].upper()
            if cmd == self.NEW:
                self.do_new()
            elif cmd == self.END:
                break
            elif cmd in self.current_composer.SGL_GATES:
                self.do_sgl(tokens)
            elif cmd in self.current_composer.SGL_GATES_PARAM:
                self.do_sgl_param(tokens)
            elif cmd in self.current_composer.TWO_GATES:
                self.do_two(tokens)
        print("Random circuit done")
        

    def random_command(self, n):
        p_s = 0.3
        p_sr = 0.4
        p_t = 0.3
        selection = choice(['s', 'sr', 't'], p=[p_s, p_sr, p_t])
        if selection == 's':
            gate = choice(['x','y','z','h'], p=[0.15, 0.15, 0.15, 0.55])
            idx = randint(0, n-1)
            return [gate, idx]
        elif selection == 'sr':
            gate = choice(['rx','ry','rz'])
            idx = randint(0, n-1)
            param = random()*2*pi
            return [gate, idx, param]
        else:
            gate = choice(['cx','cz'])
            idx_src, idx_dst = choice(range(n), size=2, replace=False) 
            return [gate, idx_src, idx_dst]
            

    def do_help(self):
        help_message = """USAGE:
Single qubit gate: [gate] [index]
\tEg: x 1
Single qubit gate param: [gate] [index] [param]
\tEg: rx 0 0.5
Two qubit gate: [gate] [control] [target]
\tEg: cx 0 1
Begin new note: NEW
Finish composer: END
View all the circuits: VIEWALL
        """
        print(help_message)
    
    def do_new(self):
        self.current_composer.new_note()
    
    def do_end(self):
        pass
    
    def do_error(self):
        print("Incorrect format. Enter 'HELP' to view options")
    
    def do_sgl(self, tokens):
        gate = tokens[0]
        try:
            idx = int(tokens[1])
            self.current_composer.add_single_qubit_gate(gate, idx)
        except:
            self.do_error()        
    
    def do_sgl_param(self, tokens):
        gate = tokens[0]
        try:
            idx = int(tokens[1])
            param = float(tokens[2])
            self.current_composer.add_single_qubit_gate_wparam(gate, idx, param)
        except:
            self.do_error()        
    
    def do_two(self, tokens):
        gate = tokens[0]
        try:
            idx_src = int(tokens[1])
            idx_dst = int(tokens[2])
            self.current_composer.add_two_qubit_gate(gate, idx_src, idx_dst)
        except:
            self.do_error()
    

if __name__ == "__main__":
    #testing
    sandbox = Sandbox_CLI()
    sandbox.init_composer('test')
    sandbox.construct_composer_random(12)
    sandbox.current_composer.dump()

    for i in range(2):
        sandbox.current_composer.run_job()
        sandbox.current_composer.generate_audio()