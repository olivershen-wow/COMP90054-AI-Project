from captureAgents import CaptureAgent
import pickle
# STEP 1: import
from State_1 import State_1


def createTeam(firstIndex, secondIndex, isRed, first = 'RecordAgent', second = 'RecordAgent'):
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

class RecordAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.agentActions = pickle.load(open('./replayAgentActions','rb'), encoding="bytes")
        self.action = [action for i, action in enumerate(self.agentActions) if self.index == action[0]]

        # STEP 2: Initial variables
        self.initState = State_1(self, gameState).getInitialStates_1()
        self.previousState = {0: [], 1: [], 2: [], 3: []}

    def chooseAction(self, gameState):
        # STEP 3: Get state features
        currentState = State_1(self, gameState).getState_1(self.initState)
        row = self.previousState[self.index] + currentState
        self.previousState[self.index] = currentState

        # STEP 4: Append each row to a list (?)
        print(row) if len(row) > len(currentState) else None
        ##################################################################
        return self.action.pop(0)[1]

