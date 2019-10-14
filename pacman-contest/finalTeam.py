# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

import sys

sys.path.append('teams/kdbnb/')

import copy
from util import manhattanDistance
import InitialMap
from captureAgents import CaptureAgent
import random, time, util
from game import *
import game
from layout import Grid
import myProblem
from State_1 import *
import random, collections, time
import getEnemyPosition
import util
import gameData
#################
# Team creation #
#################
debug = False
# debug = True
enemyPosition = getEnemyPosition.enemyPosition()
gameData = gameData.gamedata()
deadEnemy = {}
teammateState = {}
enemyCarryFoodNumber = collections.defaultdict(float)
actionHistory = {}
agentMod = {}
positionHistory  ={}

def createTeam(firstIndex, secondIndex, isRed,
               first='AttackAgent', second='AttackAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.  isRed is True if the red team is being created, and
    will be False if the blue team is being created.

    As a potentially helpful development aid, this function can take
    additional string-valued keyword arguments ("first" and "second" are
    such arguments in the case of this function), which will come from
    the --redOpts and --blueOpts command-line arguments to capture.py.
    For the nightly contest, however, your team will be created without
    any extra arguments, so you should make sure that the default
    behavior is what you want for the nightly contest.
    """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########


class AttackAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)  # must be put ahead to set value of self.red
        self.walls = gameState.getWalls()
        self.mapMatrix = self.getMapMatrix(gameState)
        self.midX = self.getMiddleX(gameState)
        self.enemyMidX = self.getEnemyMiddleX(gameState)
        self.ourRegionX = range(0, self.midX + 1) if self.red else range(self.midX, len(self.mapMatrix[0]))
        self.enemyRegionX = range(self.midX + 1, len(self.mapMatrix[0])) if self.red else range(0, self.midX)
        self.midLine = self.getMiddleLine(gameState)
        self.enemyMidLine = self.getEnemyMiddleLine(gameState)
        self.capsules = self.getCapsules(gameState)
        self.deadEnd = InitialMap.searchDeadEnd(self.mapMatrix)  # keys are deadEnds, values are corresponding depth
        self.sumOfFood = len(self.getFood(gameState).asList())
        # used for separate pacman
        self.randomFoodIndex = random.randint(0, self.sumOfFood - 1)
        self.manhattanSight = self.getManhattanSight()
        self.randomSelectFood = True
        self.allienIndex = (self.index + 2) % 4
        self.lastAction = None
        # list of Xs of region for different sidee
        if self.red:
            self.enemyIndex = [1, 3]
            deadEnemy[1] = 0
            deadEnemy[3] = 0
        else:
            self.enemyIndex = [0, 2]
            deadEnemy[0] = 0
            deadEnemy[2] = 0
        if gameState.data.timeleft == 1200:
            enemyPosition.start = True
            enemyPosition.initial(gameState, self.red, self.mapMatrix)
        self.enemyDied = {}
        self.enemyDied[self.enemyIndex[0]] = False
        self.enemyDied[self.enemyIndex[1]] = False

        actionHistory[self.index] = []
        agentMod[self.index] = []

    def getMapMatrix(self, gameState):
        """
        Start counting from the top-left corner

        0 1 2 ➡
        1
        2
        ⬇

        0: Walls
        1: Available movements
        2: RedFood
        3: RedCapsule
        4: BlueFood
        5: BlueCapsule
        """
        mapMatrix = gameState.deepCopy().data.layout.layoutText
        mapHeight = len(mapMatrix)
        for i in range(mapHeight):
            mapMatrix[i] = mapMatrix[i].replace('%', '0')
            mapMatrix[i] = mapMatrix[i].replace(' ', '1')
            mapMatrix[i] = mapMatrix[i].replace('.', '1')
            mapMatrix[i] = mapMatrix[i].replace('o', '1')
            mapMatrix[i] = mapMatrix[i].replace('1', '1')
            mapMatrix[i] = mapMatrix[i].replace('2', '1')
            mapMatrix[i] = mapMatrix[i].replace('3', '1')
            mapMatrix[i] = mapMatrix[i].replace('4', '1')
            mapMatrix[i] = list(mapMatrix[i])
            mapMatrix[i] = list(map(float, mapMatrix[i]))
        for redFood in gameState.getRedFood().asList():
            x = redFood[0]
            y = mapHeight - 1 - redFood[1]
            mapMatrix[y][x] = 2.0
        for redCapsule in gameState.getRedCapsules():
            if not redCapsule:
                continue
            x = redCapsule[0]
            y = mapHeight - 1 - redCapsule[1]
            mapMatrix[y][x] = 3.0
        for blueFood in gameState.getBlueFood().asList():
            x = blueFood[0]
            y = mapHeight - 1 - blueFood[1]
            mapMatrix[y][x] = 4.0
        for blueCapsule in gameState.getBlueCapsules():
            if not blueCapsule:
                continue
            x = blueCapsule[0]
            y = mapHeight - 1 - blueCapsule[1]
            mapMatrix[y][x] = 5.0
        return mapMatrix

    def getMiddleX(self, gameState):
        mapWidth = gameState.data.layout.width
        if self.red:
            x = int((mapWidth - 2) / 2)
        else:
            x = int((mapWidth - 2) / 2 + 1)
        return x

    def getEnemyMiddleX(self, gameState):  # x of middle line on enemy's side
        mapWidth = gameState.data.layout.width
        if self.red:
            enemyX = int((mapWidth - 2) / 2 + 1)
        else:
            enemyX = int((mapWidth - 2) / 2)
        return enemyX

    def getMiddleLine(self, gameState):
        midLine = []
        mapHeight = gameState.data.layout.height
        x = self.midX
        wallList = gameState.getWalls().asList()
        for y in range(1, mapHeight):
            if (x, y) not in wallList:
                midLine.append((x, y))
        return midLine

    def getEnemyMiddleLine(self, gameState):
        enemyMidLine = []
        mapHeight = gameState.data.layout.height
        x = self.enemyMidX
        wallList = gameState.getWalls().asList()
        for y in range(1, mapHeight):
            if (x, y) not in wallList:
                enemyMidLine.append((x, y))
        return enemyMidLine

    def getIndex(self, index):  # 0:self;2:teammate;1/3:enemy
        new_index = index + self.index
        if new_index > 3:
            new_index = new_index - 4
        return new_index

    def getMinDistToEnemy(self, curPos, enemyList):
        curMinDist = 99999
        for enemy in enemyList:
            dist = self.distancer.getDistance(enemy, curPos)
            curMinDist = min(dist, curMinDist)
        return curMinDist

    def getAgentIndexCloseToTarget(self, gameState, curPos, teammatePos, targetList):
        curMinDist = 99999
        for target in targetList:
            dist = self.distancer.getDistance(curPos, target)
            curMinDist = min(dist, curMinDist)
        teammateMinDist = 99999
        for target in targetList:
            dist = self.distancer.getDistance(teammatePos, target)
            teammateMinDist = min(dist, teammateMinDist)
        if curMinDist <= teammateMinDist:
            return self.index
        else:
            return self.getIndex(2)

    # def capsuleEatenLastMove(self, gameState):
    #   prevGameState = self.getPreviousObservation()
    #   if prevGameState != None:
    #     prevCapsules = self.getCapsules(prevGameState)
    #     curCapsules = self.getCapsules(gameState)
    #     for capsule in prevCapsules:
    #       if capsule not in curCapsules:
    #         return True
    #   return False

    def pacmanEnemy(self, enemyList):
        res = []
        for pos in enemyList:
            if pos != None and pos[0] in self.ourRegionX:
                res.append(pos)
        return res

    def ghostEnemy(self, enemyList):
        res = []
        for pos in enemyList:
            if pos != None and pos[0] in self.enemyRegionX:
                res.append(pos)
        return res

    def enemySucide(self, gameState):
        eatEnemy = {}
        for i in self.enemyIndex:
            eatEnemy[i] = False
        if gameState.data.timeleft < 1190:
            preGameState = self.getPreviousObservation()
            curPos = gameState.getAgentPosition(self.index)
            curPosTeammate = gameState.getAgentPosition(self.allienIndex)
            for enemyIndex in self.enemyIndex:
                curPosE = gameState.getAgentPosition(enemyIndex)
                prePosE = preGameState.getAgentPosition(enemyIndex)
                if curPosE is None and (not prePosE is None):
                    distance1 = self.distancer.getDistance(curPos, prePosE)
                    distance2 = self.distancer.getDistance(curPosTeammate, prePosE)
                    if (distance1 == 1) or (distance2 == 1):
                        eatEnemy[enemyIndex] = True
        return eatEnemy

    def eatEnemy1(self, gameState, action):
        eatEnemy = {}
        nextGameState = gameState.generateSuccessor(self.index, action)
        nextPos = nextGameState.getAgentPosition(self.index)
        for index in self.enemyIndex:
            curPosE = gameState.getAgentPosition(index)
            nextPosE = nextGameState.getAgentPosition(index)
            # if debug:
            #     print("Sel next pos:", nextPos, "Enemy Current", curPosE, "Enemy Next", nextPosE)
            if (gameState.getInitialAgentPosition(index) == nextPosE):
                eatEnemy[index] = True
            else:
                eatEnemy[index] = False
        return eatEnemy

    def eatEnemy(self, gameState):
        eatEnemy = {}
        preGameState = self.getPreviousObservation()
        for index in self.enemyIndex:
            eatEnemy[index] = False
            if gameState.data.timeleft < 1190:
                enemyCur = gameState.getAgentPosition(index)
                enemyPre = preGameState.getAgentPosition(index)
                posPre = preGameState.getAgentPosition(self.index)
                allienPre = preGameState.getAgentPosition(self.allienIndex)
                if enemyCur is None and (not enemyPre is None) and (
                    gameState.getAgentPosition(self.index) != gameState.getInitialAgentPosition(self.index)):
                    distance = self.distancer.getDistance(posPre, enemyPre)
                    distance2 = self.distancer.getDistance(allienPre, enemyPre)
                    if (distance < 2) or (distance2 < 2):
                        eatEnemy[index] = True
                    else:
                        eatEnemy[index] = False
                else:
                    if (not enemyPre is None) and (enemyCur is None):
                        distance = self.distancer.getDistance(posPre, enemyPre)
                        if distance > 2:
                            eatEnemy[index] = True
                        else:
                            eatEnemy[index] = False
                    else:
                        eatEnemy[index] = False
        return eatEnemy

    def getEnemyTrueP(self, gameState):
        enemyPosition = {}
        if self.red:
            enemyPosition[1] = gameState.getAgentPosition(1)
            enemyPosition[3] = gameState.getAgentPosition(3)
        else:
            enemyPosition[0] = gameState.getAgentPosition(0)
            enemyPosition[2] = gameState.getAgentPosition(2)
        return enemyPosition

    def foodBeenEaten(self, gameState):
        if gameState.data.timeleft < 1190:
            curFoods = self.getFoodYouAreDefending(gameState).asList()
                                                  # self.getPreviousObservation()
            preFoods = self.getFoodYouAreDefending(teammateState[self.allienIndex]).asList()
        else:
            return set()
        return set(preFoods) - set(curFoods)

    def capsuleBeenEaten(self, gameState):
        if gameState.data.timeleft < 1190:
            curCap = self.getCapsulesYouAreDefending(gameState)
            preCap = self.getCapsulesYouAreDefending(self.getPreviousObservation())
        else:
            return set()
        return set(preCap) - set(curCap)

    def getEnemyPosition(self, gameState):
        curPos = gameState.getAgentPosition(self.index)
        noiseDistance = gameState.agentDistances
        if gameState.data.timeleft < 1200:
            eatEnemy = self.enemySucide(gameState)
            for i in eatEnemy:
                if eatEnemy[i] and deadEnemy[i] == 0:
                    enemyPosition.updateWithDeath(i)
                    deadEnemy[i] = 4
                else:
                    enemyPosition.updateWithNoise(noiseDistance, self.index, curPos, i)
            enemyTruePosition = self.getEnemyTrueP(gameState)
            for i in enemyTruePosition:
                if not enemyTruePosition[i] is None:
                    enemyPosition.updateWithVision(i, enemyTruePosition[i])
            if len(self.foodBeenEaten(gameState)) != 0:
                enemyPosition.updateWithEatenFood(list(self.foodBeenEaten(gameState))[0])
            if len(self.capsuleBeenEaten(gameState)) != 0:
                enemyPosition.updateWithEatenFood(list(self.capsuleBeenEaten(gameState))[0])
            a = enemyPosition.enemyPosition
        #     return a
        # return {}

    def getEnemyInRegion(self, gameState, enemyPosition):
        enemyInRegion = {}
        enemy = {}
        for index in self.enemyIndex:
            enemyInRegion[index] = [0,0]
            for pos in enemyPosition[index]:
                if pos[0] in self.ourRegionX:
                    enemyInRegion[index][0] += 1
                else:
                    enemyInRegion[index][1] +=1
            total = enemyInRegion[index][0]+enemyInRegion[index][1]
            pro = enemyInRegion[index][0]/total
            print(enemyInRegion[index][0],enemyInRegion[index][1])
            if pro>0.8:
                enemy[index] = "Our"
            else:
                if pro > 0.5:
                    enemy[index] = "Mid"
                else:
                    enemy[index] = "Enemy"
        return enemy

    def updateDeath(self, gameState, action):
        enemyDeath = self.eatEnemy1(gameState, action)
        for i in enemyDeath:
            if enemyDeath[i]:
                enemyPosition.updateWithDeath(i)
                deadEnemy[i] = 4

    def getBlockRegions(self, gameState):
        block = []
        cur = gameState.getAgentPosition(self.index)
        for i in self.enemyIndex:
            enemy = gameState.getAgentPosition(i)
            if not enemy is None:
                enemyDistance = self.distancer.getDistance(cur, enemy)
                depth = enemyDistance / 2
                for cell in self.deadEnd:
                    if self.deadEnd[cell] >= depth:
                        block.append(cell)
        return list(set(block))

    def getNeedOfDefenceEnemyPosition(self, gameState, enemyPosition):
        curFoods = self.getFoodYouAreDefending(gameState).asList()
        enemyPositionDict = {}
        for index in self.enemyIndex:
            minDis = 999999
            minPos = None
            for food in curFoods:
                for pos in enemyPosition[index]:
                    dis = self.distancer.getDistance(food, pos)
                    if dis < minDis:
                        minDis = dis
                        minPos = pos
            enemyPositionDict[index] = minPos
        # if debug:
        #     for i in enemyPositionList:
        #         self.debugDraw(i, [.9,0,0]) if i else None
        return enemyPositionDict

    def getFoodFarFromEnemy(self, gameState, curPos, enemyPositionToDefend):
        curFoods = self.getFood(gameState).asList()
        minDis = 999999
        minPos = None
        enemyList = []
        for i in enemyPositionToDefend:
            enemyList.append(enemyPositionToDefend[i])
        for i in curFoods:
            distanceToFood = self.distancer.getDistance(curPos, i)
            distanceToGhost = min(map(lambda x: self.distancer.getDistance(x, curPos), enemyList))
            dis = distanceToFood - distanceToGhost
            if dis < minDis:
                minDis = dis
                minPos = i
        # if debug:
        #     self.debugDraw(minPos, [.98,.41,.07]) if minPos else None
        return minPos

    def getMiddleLinePositionToDefend(self, gameState, enemyPositionToDefend):
        curFoods = self.getFood(gameState).asList()
        maxDis = float("-inf")
        maxPos = None
        enemyList = []
        for i in enemyPositionToDefend:
            enemyList.append(enemyPositionToDefend[i])
        for i in curFoods:
            for j in self.midLine:
                distanceToFood = self.distancer.getDistance(j, i)
                distanceToGhost = min(map(lambda x: self.distancer.getDistance(x, j), enemyList))
                dis = distanceToGhost - distanceToFood
                if dis > maxDis:
                    maxDis = dis
                    maxPos = j
        if self.index ==1:
            self.debugDraw(maxPos,[0,1,0])
        return maxPos

    def getManhattanSight(self):
        v = []
        for i in range(-5,6):
            for j in range(-5, 6):
                if abs(i) + abs(j) <= 5:
                    v.append((i,j))
        return v

    def getEnemySight(self, enemyPosition):
        sights = {}
        sight = collections.defaultdict(int)
        for index in self.enemyIndex:
            for enemyX, enemyY in enemyPosition[index]:
                for sightX, sightY in self.manhattanSight:
                    s = (enemyX + sightX, enemyY + sightY)
                    sight[s] += 1
            sights[index] = sight
        return sights

    def scoreChanged(self, gameState):
        myCurScore = 0
        teammateNextMoveScore = 0
        if gameState.data.timeleft < 1190:
            myCurScore = gameState.data.score
            teammateNextMoveScore = teammateState[self.allienIndex].data.score
        scoreChange = myCurScore - teammateNextMoveScore
        return scoreChange

    def getEnemyCarryFoodNumber(self, gameState, enemyPosition):
        enemyKeys = list(enemyPosition.keys())
        foodBeenEaten = list(self.foodBeenEaten(gameState))
        if len(foodBeenEaten) != 0:
            food = foodBeenEaten[0]
            if food in enemyPosition[enemyKeys[0]] and food not in enemyPosition[enemyKeys[1]]:
                enemyCarryFoodNumber[enemyKeys[0]] += 1
            elif food in enemyPosition[enemyKeys[1]] and food not in enemyPosition[enemyKeys[0]]:
                enemyCarryFoodNumber[enemyKeys[1]] += 1
            elif food in enemyPosition[enemyKeys[0]] and food in enemyPosition[enemyKeys[1]]:
                enemyCarryFoodNumber[enemyKeys[1]] += 0.5
        scoreChanged = self.scoreChanged(gameState)
        if scoreChanged:
            for pos in enemyPosition[enemyKeys[0]]:
                if pos in self.enemyMidLine:
                    enemyCarryFoodNumber[enemyKeys[0]] = 0
            for pos in enemyPosition[enemyKeys[1]]:
                if pos in self.enemyMidLine:
                    enemyCarryFoodNumber[enemyKeys[1]] = 0
        if deadEnemy[enemyKeys[0]]:
            enemyCarryFoodNumber[enemyKeys[0]] = 0
        if deadEnemy[enemyKeys[1]]:
            enemyCarryFoodNumber[enemyKeys[1]] = 0

    def getClostestMidDistance(self,curPos,gameState):
        minDist = 999
        for i in self.midLine:
            dist = self.distancer.getDistance(curPos,i)
            if minDist > dist:
                minDist = dist
                closestMid = i
        return minDist,closestMid

    def updateEnemyDied(self):
        for index in self.enemyDied:
            if self.enemyDied[index]:
                if self.enemyInRegion[index] != "Enemy":
                    self.enemyDied[index] = False
            else:
                if deadEnemy[index]> 0:
                    self.enemyDied[index] = True
                else:
                    self.enemyDied[index] = False
                if self.enemyDied[index]:
                    print("enemy Died")

    def getSafeFood(self,gameState,block):
        foodList = self.getFood(gameState).asList()
        return list(set(foodList) - set(block))

    def getEnemyAllatHome(self):
        enemyAllHome = True
        for enemy in self.enemyInRegion:
            enemyAllHome = enemyAllHome & (self.enemyInRegion[enemy] != "Our")
        return enemyAllHome

    def getEnemyNeedToTrace(self):
        minDist = 9999
        for index in self.enemyIndex:
            if self.enemyInRegion[index] == "Our":
                minDist = min(minDist,self.distancer.getDistance(self.enemyPositionsToDefend[index],self.curPos))
                enemy = index
        return enemy

    def getClosedFood(self,gameState,teammateTarget):
        minDist = 999
        foods = self.getFood(gameState).asList()
        food = foods[0]
        foods = list(set(foods) - set(teammateTarget))
        for i in foods:
            dist = self.distancer.getDistance(i,self.curPos)
            if dist < minDist:
                food = i
                minDist = dist
        return food

    def getTeammateTargetRegion(self,gameState):
        foodCluster = []
        if agentMod[self.allienIndex] != []:
            if agentMod[self.allienIndex][0] == "eatFood":
                foodCluster = InitialMap.cluster1(gameState,agentMod[self.allienIndex][1],self)
                # self.debugClear()
                # for i in foodCluster:
                #     self.debugDraw(i,[0.3,self.index / 4,.5])
                # self.debugDraw(agentMod[self.allienIndex][1],[0.9,0.6,0.1])
        return foodCluster

    def getEnemyInsightTogether(self,enemyInsight):
        posInsight = {}
        for i in enemyInsight:
            for j in enemyInsight[i]:
                if j in posInsight:
                    posInsight[j] = posInsight[j] + enemyInsight[i][j]
                else:
                    posInsight[j] = enemyInsight[i][j]
        return posInsight

    def getFoodsAroundCapsules(self, gameState):
        d = dict()
        foodList = self.getFood(gameState).asList()
        for capsule in self.capsules:
            l = []
            for food in foodList:
                if self.distancer.getDistance(food, capsule) <= 20:
                    l.append(food)
            d[capsule] = l
        return d

    def getCapsuleScore(self, gameState):
        foodList = self.getFood(gameState).asList()
        d = collections.defaultdict(int)
        deadEnd = self.deadEnd.keys()
        for capsule in self.capsules:
            for food in foodList:
                if self.distancer.getDistance(food, capsule) <= 20:
                    if food in deadEnd:
                        d[capsule] += self.deadEnd[food]
        return d

    def curInsightOfEnemy(self, curPos, enemyList):
        insight = False
        for enemy in enemyList:
            if enemy != None:
                insight = insight or (manhattanDistance(curPos, enemy) <= 5)
        return insight

    def curCloseToEnemy(self, curPos, enemyList):
        close = False
        for enemy in enemyList:
            if not (enemy is None):
                close = close or (self.distancer.getDistance(curPos, enemy) <= 2)
        return close

    ####################################################################################################################
    def chooseAction(self, gameState):
        if debug:
            self.debugClear()
        self.curPos = gameState.getAgentPosition(self.index)
        teammateCluster = self.getTeammateTargetRegion(gameState)
        closestFood = self.getClosedFood(gameState,teammateCluster)
        enemyIndices = self.getOpponents(gameState)
        enemyPos = []
        for idx in enemyIndices:
            enemyPos.append(gameState.getAgentPosition(idx))
        self.foodGrid = self.getFood(gameState)
        self.carryFoods = gameState.data.agentStates[self.index].numCarrying
        teammateIndex = self.getIndex(2)
        teammatePos = gameState.getAgentPosition(teammateIndex)

        return 'Stop'

    def aStarSearch(self, problem, gameState, heuristic, timeLimit):
        start = time.clock()
        """Search the node that has the lowest combined cost and heuristic first."""
        # init
        visited = set()
        best_g = dict()
        """state: [position, foodGrid, food]"""
        """state, action list, cost value g"""
        start_node = (problem.getStartState(gameState, self.foodGrid), [], 0)
        frontier = util.PriorityQueue()
        priority = heuristic(problem.getStartState(gameState, self.foodGrid))  # f = h + g(start is 0)
        frontier.push(start_node, priority)

        while not frontier.isEmpty():
            elapsed = (time.clock() - start)
            if elapsed >= timeLimit:
                if debug:
                    print("Time used:", elapsed)
                    print("time exceed")
                return "TIMEEXCEED", None  # for eatOneSafeFood time exceed
            else:
                current_node = frontier.pop()
                if current_node[0] in best_g.keys():  # reopen
                    if best_g[current_node[0]] > current_node[2]:
                        best_g[current_node[0]] = current_node[2]
                        for successor in problem.getSuccessors(current_node[0]):
                            cost_g = current_node[2] + successor[2]
                            priority = cost_g + heuristic(successor[0])
                            path = current_node[1] + [successor[1]]
                            frontier.push((successor[0], path, cost_g), priority)
                elif current_node[0] not in visited:
                    best_g[current_node[0]] = current_node[2]
                    visited.add(current_node[0])
                    if problem.isGoalState(gameState, current_node[0]):
                        return current_node[1], current_node[0][0]
                    else:
                        for successor in problem.getSuccessors(current_node[0]):
                            cost_g = current_node[2] + successor[2]
                            priority = cost_g + heuristic(successor[0])
                            path = current_node[1] + [successor[1]]
                            frontier.push((successor[0], path, cost_g), priority)
        return None, None