import os
path = os.path

from myhdl import *
from myhdl.test import verifyConversion

# SEARCH, CONFIRM, SYNC = range(3)
ACTIVE_LOW = bool(0)
FRAME_SIZE = 8
t_State_b = enum('SEARCH', 'CONFIRM', 'SYNC')
t_State_oh = enum('SEARCH', 'CONFIRM', 'SYNC', encoding="one_hot")
t_State_oc = enum('SEARCH', 'CONFIRM', 'SYNC', encoding="one_cold")

def FramerCtrl(SOF, state, syncFlag, clk, reset_n, t_State):
    
    """ Framing control FSM.

    SOF -- start-of-frame output bit
    state -- FramerState output
    syncFlag -- sync pattern found indication input
    clk -- clock input
    reset_n -- active low reset
    
    """
    
    index = Signal(intbv(0)[8:]) # position in frame

    @always(clk.posedge, reset_n.negedge)
    def FSM():
        if reset_n == ACTIVE_LOW:
            SOF.next = 0
            index.next = 0
            state.next = t_State.SEARCH
        else:
            index.next = (index + 1) % FRAME_SIZE
            SOF.next = 0
            if state == t_State.SEARCH:
                index.next = 1
                if syncFlag:
                    state.next = t_State.CONFIRM
            elif state == t_State.CONFIRM:
                if index == 0:
                    if syncFlag:
                        state.next = t_State.SYNC
                    else:
                        state.next = t_State.SEARCH
            elif state == t_State.SYNC:
                if index == 0:
                    if not syncFlag:
                        state.next = t_State.SEARCH
                SOF.next = (index == FRAME_SIZE-1)
            else:
                raise ValueError("Undefined state")
            
    return FSM


def FramerCtrl_alt(SOF, state, syncFlag, clk, reset_n, t_State):
    
    """ Framing control FSM.

    SOF -- start-of-frame output bit
    state -- FramerState output
    syncFlag -- sync pattern found indication input
    clk -- clock input
    reset_n -- active low reset
    
    """
    
 
    def FSM():
        index = intbv(0)[8:] # position in frame
        state_var = t_State.SEARCH
        while True:
            yield clk.posedge, reset_n.negedge
            if reset_n == ACTIVE_LOW:
                SOF.next = 0
                index[:] = 0
                state_var = t_State.SEARCH
                state.next = t_State.SEARCH
            else:
                SOF_var = 0
                if state == t_State.SEARCH:
                    index[:] = 0
                    if syncFlag:
                        state_var = t_State.CONFIRM
                elif state == t_State.CONFIRM:
                    if index == 0:
                        if syncFlag:
                            state_var = t_State.SYNC
                        else:
                            state_var = t_State.SEARCH
                elif state == t_State.SYNC:
                    if index == 0:
                        if not syncFlag:
                            state_var = t_State.SEARCH
                    SOF_var = (index == FRAME_SIZE-1)
                else:
                    raise ValueError("Undefined state")
                index[:]= (index + 1) % FRAME_SIZE
                SOF.next = SOF_var
                state.next = state_var

    FSM_1 = FSM()
    return FSM_1


def FramerCtrl_ref(SOF, state, syncFlag, clk, reset_n, t_State):
    
    """ Framing control FSM.

    SOF -- start-of-frame output bit
    state -- FramerState output
    syncFlag -- sync pattern found indication input
    clk -- clock input
    reset_n -- active low reset
    
    """
    
    index = intbv(0, min=0, max=8) # position in frame
    while 1:
        yield clk.posedge, reset_n.negedge
        if reset_n == ACTIVE_LOW:
            SOF.next = 0
            index[:] = 0
            state.next = t_State.SEARCH
        else:
            SOF.next = 0
            if state == t_State.SEARCH:
                index[:] = 0
                if syncFlag:
                    state.next = t_State.CONFIRM
            elif state == t_State.CONFIRM:
                if index == 0:
                    if syncFlag:
                        state.next = t_State.SYNC
                    else:
                        state.next = t_State.SEARCH
            elif state == t_State.SYNC:
                if index == 0:
                    if not syncFlag:
                        state.next = t_State.SEARCH
                SOF.next = (index == FRAME_SIZE-1)
            else:
                raise ValueError("Undefined state")
            index[:]= (index + 1) % FRAME_SIZE


    
    
def FSMBench(FramerCtrl, t_State):

    SOF = Signal(bool(0))
    SOF_v = Signal(bool(0))
    syncFlag = Signal(bool(0))
    clk = Signal(bool(0))
    reset_n = Signal(bool(1))
    state = Signal(t_State.SEARCH)
    state_v = Signal(intbv(0)[8:])

    framerctrl_inst = FramerCtrl(SOF, state, syncFlag, clk, reset_n, t_State)

    def clkgen():
        clk.next = 0
        reset_n.next = 1
        yield delay(10)
        reset_n.next = 0
        yield delay(10)
        reset_n.next = 1
        yield delay(10)
        for i in range(1000):
            yield delay(10)
            clk.next = not clk

    table = (12, 8, 8, 4, 11, 8, 8, 7, 6, 8, 8)

    def stimulus():
        for i in range(3):
            yield clk.posedge
        for i in range(len(table)):
            n = table[i]
            syncFlag.next = 1
            yield clk.posedge
            syncFlag.next = 0
            for i in range(n-1):
                yield clk.posedge
        raise StopSimulation

    def check():
        while True:
            yield clk.negedge
            print state
            # print clk
#            print state
            # print "MyHDL: %s %s" % (SOF, hex(state))
            # print "Verilog: %s %s" % (SOF_v, hex(state_v))

    return framerctrl_inst,  clkgen(), stimulus(), check()


verifyConversion(FSMBench, FramerCtrl, t_State_b)

## def testRef(self):
##     for t_State in (t_State_b, t_State_oc, t_State_oh):
##         tb_fsm = self.bench(FramerCtrl_ref, t_State)
##         sim = Simulation(tb_fsm)
##         sim.run()



## def testAlt(self):
##     for t_State in (t_State_b, t_State_oc, t_State_oh):
##         tb_fsm = self.bench(FramerCtrl_alt, t_State)
##         sim = Simulation(tb_fsm)
##         sim.run()

## def testDoc(self):
##     tb_fsm = self.bench(FramerCtrl, t_State_oh)
##     sim = Simulation(tb_fsm)
##     sim.run()
