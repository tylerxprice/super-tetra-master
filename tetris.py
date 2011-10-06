import os, pygame, sys, math, random
from pygame.locals import *
from events import *
from utilities import Utilities, Callable

if not pygame.font: print 'Warning, fonts disabled'
if not pygame.mixer: print 'Warning, sound disabled'


TITLE_CAPTION = "Super Tetra Master"
SCREEN_RESOLUTION = (640,480)
FRAMES_PER_SECOND = 60



HOLD_ORIGIN = (240, 32)
NEXT_ORIGINS = ((292, 20), (362, 40), (400, 40))
WELL_ORIGIN = (240,48) #pixels
TILE_SIZE = (16,16) #pixels
SMALL_TILE_SIZE = (8, 8)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
ORANGE = (255, 153, 51)
GREY = (100, 100, 100)


DIRECTION_UP = 0
DIRECTION_DOWN = 1
DIRECTION_LEFT = 2
DIRECTION_RIGHT = 3
DIRECTION_CW = 4
DIRECTION_CCW = 5



class EventManager:
    """class that coordinates communication between the model and the view and controller"""
    def __init__(self):
        from weakref import WeakKeyDictionary
        self.listeners = WeakKeyDictionary()
        self.eventQueue = []

    def RegisterListener(self, listener):
        self.listeners[listener] = 1

    def UnregisterListener(self, listener):
        if listener in self.listeners:
            del self.listeners[listener]

    def Post(self, event):
        """post a new event, broadcast to all listeners"""
        self.eventQueue.append(event)
        if isinstance(event, TickEvent):
            self.ConsumeEventQueue()
        
    def ConsumeEventQueue(self):
        i = 0;
        while i < len(self.eventQueue):
            event = self.eventQueue[i]
            for listener in self.listeners:
                listener.Notify(event)
            i += 1

        # all events handled, clear queue
        self.eventQueue = []


class KeyboardController:
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)

        #pygame.event.set_allowed([KEYDOWN])
        pygame.key.set_repeat(250, 20)

    def Notify(self, event):
        if isinstance(event, TickEvent):
            #Handle Input
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.eventManager.Post(QuitEvent())

                elif event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.eventManager.Post(QuitEvent())

                elif event.type == KEYDOWN and event.key == K_1:
                    self.eventManager.Post(TetradRotateRequest(DIRECTION_CCW))

                elif event.type == KEYDOWN and event.key == K_2:
                    self.eventManager.Post(TetradRotateRequest(DIRECTION_CW))

                elif event.type == KEYDOWN and event.key == K_BACKQUOTE:
                    self.eventManager.Post(TetradSwapRequest())
 
                elif event.type == KEYDOWN and event.key == K_DOWN:
                    self.eventManager.Post(TetradMoveRequest(DIRECTION_DOWN))
 
                elif event.type == KEYDOWN and event.key == K_UP:
                    self.eventManager.Post(SonicDropRequest())

                elif event.type == KEYDOWN and event.key == K_LEFT:
                    self.eventManager.Post(TetradMoveRequest(DIRECTION_LEFT))

                elif event.type == KEYDOWN and event.key == K_RIGHT:
                    self.eventManager.Post(TetradMoveRequest(DIRECTION_RIGHT))

                elif event.type == KEYDOWN and event.key == K_RETURN:
                    print 'start game'
                    self.eventManager.Post(GameStartRequest())


class CPUSpinnerController:
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)
        self.keepGoing = True
        self.clock = pygame.time.Clock()
        self.running = True

    def Run(self):
        while self.keepGoing:
            self.clock.tick(FRAMES_PER_SECOND)
            if self.running:
                self.eventManager.Post(TickEvent())

    def Notify(self, event):
        if isinstance(event, QuitEvent):
            self.keepGoing = False





class BlockSprite(pygame.sprite.Sprite):
    """..."""
    def __init__(self, block, colour, group=None):
        pygame.sprite.Sprite.__init__(self, group)

        surf = pygame.Surface((15,15))
        surf.fill(colour)

        self.image = surf
        self.rect  = surf.get_rect()

        self.block = block

        self.moveTo = None
        self.shrink = False
        self.grow = False

    def MoveTo(self, moveTo):
        self.moveTo = moveTo

    def Shrink(self):
        self.shrink = True
        
    def Grow(self):
        self.grow = True
        
    
    def update(self):
        if self.moveTo:
            self.rect.center = self.moveTo
            self.moveTo = None
        if self.shrink == True:
            surf = pygame.transform.scale(self.image, (7,7))
            self.image = surf
            self.shrink = False
        if self.grow == True:
            surf = pygame.transform.scale(self.image, (15,15))
            self.image = surf
            self.grow = False


class PygameView:

    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)

        self.window = pygame.display.set_mode(SCREEN_RESOLUTION)
        pygame.display.set_caption(TITLE_CAPTION)


        #self.background = pygame.Surface(self.window.get_size())
        #self.background.fill(BLACK)
        self.background, self.backgroundRect = Utilities.LoadImage("frame.png")

        #font = pygame.font.Font(None, 30)   #default font, 30px high
        #textImg = font.render("Press Enter", 1, WHITE)
        #self.background.blit( textImg, (0,0) )
        
        self.window.blit(self.background, self.backgroundRect)
        pygame.display.flip()

        self.backSprites = pygame.sprite.RenderUpdates()
        self.frontSprites = pygame.sprite.RenderUpdates()
        
        
    def AddTetrads(self, tetrads):
        origin = (-1, -1)
        colour = None
        blockSprite = None

        #add the next tetrads along the preview
        for tetrad in tetrads:
            colour = tetrad.GetColour()
            origin = NEXT_ORIGINS[tetrads.index(tetrad)]
            for block in tetrad.blocks:
                blockSprite = BlockSprite(block, colour, self.frontSprites)
                row, column = tetrad.GetPreviewBlockCoordinates(tetrad.blocks.index(block))
                if tetrads.index(tetrad) == 0:
                    moveRect = pygame.Rect((origin[0] + column * TILE_SIZE[0], origin[1] + row * TILE_SIZE[1]), TILE_SIZE)
                else:
                    moveRect = pygame.Rect((HOLD_ORIGIN[0] + column * SMALL_TILE_SIZE[0], HOLD_ORIGIN[1] + row * SMALL_TILE_SIZE[1]), SMALL_TILE_SIZE)
                    blockSprite.Shrink()
                
                blockSprite.MoveTo(moveRect.center)


    def AddTetrad(self, currentTetrad, nextTetrads):
        tetrad = None
        origin = (-1, -1)
        colour = None
        blockSprite = None
        
        #move currentTetrad to initial coordinates
        for block in currentTetrad.blocks:            
            self.MoveBlock(block)

        #move the next tetrads along the preview regions
        for tetrad in nextTetrads:
            origin = NEXT_ORIGINS[nextTetrads.index(tetrad)]

            if nextTetrads.index(tetrad) == 0:
                for block in tetrad.blocks:
                    blockSprite = self.GetBlockSprite(block)
                    row, column = tetrad.GetPreviewBlockCoordinates(tetrad.blocks.index(block))
                    moveRect = pygame.Rect((origin[0] + column * TILE_SIZE[0], origin[1] + row * TILE_SIZE[1]), TILE_SIZE)
                    blockSprite.MoveTo(moveRect.center)
                    blockSprite.Grow()
            
            elif nextTetrads.index(tetrad) < len(nextTetrads) - 1:
                for block in tetrad.blocks:
                    blockSprite = self.GetBlockSprite(block)
                    row, column = tetrad.GetPreviewBlockCoordinates(tetrad.blocks.index(block))
                    moveRect = pygame.Rect((origin[0] + column * SMALL_TILE_SIZE[0], origin[1] + row * SMALL_TILE_SIZE[1]), SMALL_TILE_SIZE)
                    blockSprite.MoveTo(moveRect.center)
                    
            else:
                for block in tetrad.blocks:
                    colour = tetrad.GetColour()
                    blockSprite = BlockSprite(block, colour, self.frontSprites)
                    row, column = tetrad.GetPreviewBlockCoordinates(tetrad.blocks.index(block))
                    moveRect = pygame.Rect((origin[0] + column * SMALL_TILE_SIZE[0], origin[1] + row * SMALL_TILE_SIZE[1]), SMALL_TILE_SIZE)
                    blockSprite.MoveTo(moveRect.center)
                    blockSprite.Shrink()

    def MoveTetrad(self, tetrad):
        for block in tetrad.blocks:            
            self.MoveBlock(block)

    def MoveBlock(self, block):
        blockSprite = self.GetBlockSprite(block)
        square = block.GetSquare()
        if square != None:
            row, column = square.GetCoordinates()
            moveRect = pygame.Rect((WELL_ORIGIN[0] + column * TILE_SIZE[0], WELL_ORIGIN[1] + row * TILE_SIZE[1]), TILE_SIZE)
            blockSprite.MoveTo(moveRect.center)
            
    def GrowTetrad(self, tetrad):
        for block in tetrad.blocks:
            blockSprite = self.GetBlockSprite(block)
            blockSprite.Grow()

    def HoldTetrad(self, tetrad):
        for block in tetrad.blocks:
            blockSprite = self.GetBlockSprite(block)
            row, column = tetrad.GetPreviewBlockCoordinates(tetrad.blocks.index(block))
            moveRect = pygame.Rect((HOLD_ORIGIN[0] + column * SMALL_TILE_SIZE[0], HOLD_ORIGIN[1] + row * SMALL_TILE_SIZE[1]), SMALL_TILE_SIZE)
            blockSprite.MoveTo(moveRect.center)
            blockSprite.Shrink()
            
            
            
            
    def AddGhost(self, tetrad):
        colour = tetrad.GetColour()
        for block in tetrad.blocks:
            blockSprite = BlockSprite(block, colour, self.backSprites)
            #row, column = block.GetCoordinates()
            #moveRect = pygame.Rect((WELL_ORIGIN[0] + column * TILE_SIZE[0], WELL_ORIGIN[1] + row * TILE_SIZE[1]), TILE_SIZE)
            #blockSprite.MoveTo(moveRect.center)
            
    def UpdateGhost(self, tetrad):
        for block in tetrad.blocks:
            blockSprite = self.GetBlockSprite(block)
            row, column = block.GetCoordinates()
            moveRect = pygame.Rect((WELL_ORIGIN[0] + column * TILE_SIZE[0], WELL_ORIGIN[1] + row * TILE_SIZE[1]), TILE_SIZE)
            blockSprite.MoveTo(moveRect.center)


    def GetBlockSprite(self, block):
        for s in self.frontSprites:
            if hasattr(s, "block") and s.block == block:
                return s
        for s in self.backSprites:
            if hasattr(s, "block") and s.block == block:
                return s
        

    def Notify(self, event):
        if isinstance(event, TickEvent):
            #Draw everything
            self.backSprites.clear(self.window, self.background)
            self.frontSprites.clear(self.window, self.background)
            
            self.backSprites.update()
            self.frontSprites.update()

            dirtyRects1 = self.backSprites.draw(self.window)
            dirtyRects2 = self.frontSprites.draw(self.window)
            
            dirtyRects = dirtyRects1 + dirtyRects2
            pygame.display.update( dirtyRects )


        elif isinstance(event, TetradsCreatedEvent):
            self.AddTetrads(event.tetrads)

        elif isinstance(event, TetradAddedEvent):
            self.AddTetrad(event.currentTetrad, event.nextTetrads)

        elif isinstance(event, TetradMovedEvent):
            self.MoveTetrad(event.tetrad)
            
        elif isinstance(event, SonicDropEvent):
            self.MoveTetrad(event.tetrad)

        elif isinstance(event, TetradRotatedEvent):
            self.MoveTetrad(event.tetrad)

        elif isinstance(event, TetradDroppedEvent):
            self.MoveTetrad(event.tetrad)

        elif isinstance(event, GhostAddedEvent):
            self.AddGhost(event.tetrad)
            
        elif isinstance(event, GhostUpdatedEvent):
            self.UpdateGhost(event.tetrad)

        elif isinstance(event, TetradHeldEvent):
            self.HoldTetrad(event.tetrad)
            
        elif isinstance(event, TetradSwappedEvent):
            self.GrowTetrad(event.currentTetrad)
            self.MoveTetrad(event.currentTetrad)
            self.HoldTetrad(event.holdTetrad)
            

        elif isinstance(event, StackUpdateEvent):
            for block in event.clearedBlocks:
                blockSprite = self.GetBlockSprite(block)
                self.frontSprites.remove(blockSprite)

            for block in event.movedBlocks:
                self.MoveBlock(block)



class Game:
    """..."""

    STATE_PREPARING = 0
    STATE_RUNNING = 1
    STATE_PAUSED = 2

    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)

        self.state = Game.STATE_PREPARING

        #create the players (one player for now)
        self.players = [Player(eventManager)]

    def Start(self):
        for player in self.players:
            player.Start()

        self.state = Game.STATE_RUNNING

        print "game started"
        self.eventManager.Post(GameStartedEvent(self))

    def Notify(self, event):
        if isinstance(event, GameStartRequest):
            if self.state == Game.STATE_PREPARING:
                self.Start()



class Player:

    
    NO_NEXT_TETRADS = 3
    
    """Model of the player that has a current and next tetrad"""
    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)

        #player needs a well to put the tetrads on
        self.well = Well(eventManager)

        #player's tetrads
        self.nextTetrads = range(Player.NO_NEXT_TETRADS)   
        self.holdTetrad = None


    def Start(self):        
        #create starting tetrads
        for i in range(Player.NO_NEXT_TETRADS):
            self.nextTetrads[i] = Tetrad.GetRandomTetrad(self.eventManager)
        self.eventManager.Post(TetradsCreatedEvent(self.nextTetrads))

        #build well
        self.well.Build()


    def AddTetrad(self):
        currentTetrad = self.nextTetrads.pop(0)
        self.well.AddTetrad(currentTetrad)
        self.nextTetrads.append(Tetrad.GetRandomTetrad(self.eventManager))

        self.eventManager.Post(TetradAddedEvent(currentTetrad, self.nextTetrads))


    def SwapTetrad(self):
        if self.holdTetrad == None:
             self.holdTetrad = self.well.GetCurrentTetrad()
             self.holdTetrad.ClearBlocksSquares()
             self.holdTetrad.ResetRotationState()
             self.holdTetrad.SetState(Tetrad.STATE_INACTIVE)
             self.AddTetrad()
             self.eventManager.Post(TetradHeldEvent(self.holdTetrad))

        else:
            currentTetrad = self.holdTetrad
            self.holdTetrad = self.well.GetCurrentTetrad()
            self.holdTetrad.ClearBlocksSquares()
            self.holdTetrad.ResetRotationState()
            self.holdTetrad.SetState(Tetrad.STATE_INACTIVE)
            self.well.AddTetrad(currentTetrad)
            self.eventManager.Post(TetradSwappedEvent(currentTetrad, self.holdTetrad))


    def Notify(self, event):
        if isinstance(event, GameStartedEvent):
            self.AddTetrad()

        elif isinstance(event, TetradLockedEvent):
            self.AddTetrad()

        elif isinstance(event, TetradSwapRequest):
            if self.well.GetCurrentTetrad().GetState() != Tetrad.STATE_LOCKED:
                self.SwapTetrad()
 

        

class Well:
    """Model for the well in which tetrads fall into place."""

    WELL_ROWS = 22     # two rows at top are padding for rotations
    WELL_COLUMNS = 10

    STATE_PREPARING = 0
    STATE_BUILT = 1
    
    LEVELS_FOR_LINES = (1, 2, 4, 6)

    def __init__(self, eventManager):
        self.eventManager = eventManager
        self.eventManager.RegisterListener(self)

        self.state = Well.STATE_PREPARING
        self.squares = range(Well.WELL_ROWS * Well.WELL_COLUMNS)
        self.stackedBlocks = dict()
        self.currentTetrad = None
        self.ghostTetrad = None

        self.dropTimer = 20
        self.lockTimer = 10
        
        self.lines = 0
        self.gravity = 0


    def Build(self):
        #create all the squares, give them row/column coordinates
        for row in range(Well.WELL_ROWS):
            for column in range(Well.WELL_COLUMNS):
                    self.squares[row*Well.WELL_COLUMNS + column] = Square(self.eventManager, row, column)

        #create a dictionary that keeps rows of dropped blocks for easy line detection
        for row in range(Well.WELL_ROWS):
            self.stackedBlocks[row] = list()

        self.ghostTetrad = GhostTetrad(self.eventManager)
        self.eventManager.Post(GhostAddedEvent(self.ghostTetrad))

        self.state = Well.STATE_BUILT
        self.eventManager.Post(WellBuiltEvent(self))


    def GetCurrentTetrad(self):
        return self.currentTetrad

    def AddTetrad(self, currentTetrad):
        self.currentTetrad = currentTetrad
        square = None
        row, column = (-1, -1)

        #give current tetrad blocks their initial squares
        for i in range(4):
            row, column = self.currentTetrad.GetInitialBlockCoordinates(i)
            square = self.GetSquare((row, column))
            self.currentTetrad.SetBlockSquare(i, square)
        currentTetrad.SetState(Tetrad.STATE_ACTIVE)

        self.UpdateGhostTetrad()

    def UpdateGhostTetrad(self):
        rowsDown = 1
        squares = range(4)
        canDrop = True

        # initially ghost is in the same location has current
        for i in range(4):
            self.ghostTetrad.SetBlockSquare(i, self.currentTetrad.GetBlockSquare(i))

        while canDrop:
            for block in self.currentTetrad.blocks:
                row, column = block.GetCoordinates()
                row += rowsDown
                if row >= Well.WELL_ROWS:
                    canDrop = False
                    break
                elif self.GetSquare((row, column)).IsFilled():
                    canDrop = False
                    break
                else:
                    squares[self.currentTetrad.blocks.index(block)] = self.GetSquare((row, column))

            if canDrop == True:
                for i in range(4):
                    self.ghostTetrad.SetBlockSquare(i, squares[i])

            rowsDown += 1

        self.eventManager.Post(GhostUpdatedEvent(self.ghostTetrad))


    def SonicDropCurrentTetrad(self):
        for i in range(4):
            self.currentTetrad.SetBlockSquare(i, self.ghostTetrad.GetBlockSquare(i))
            
        self.eventManager.Post(SonicDropEvent(self.currentTetrad))
            

    def DropCurrentTetrad(self):
        nextSquares = range(4)
        row, column = (-1, -1)
        canDrop = True

        #check to see if each block in the tetrad can move down        
        for i in range(4):
            row, column = self.currentTetrad.GetBlockCoordinates(i)
            row += 1
            if row >= Well.WELL_ROWS:
                canDrop = False
                break
            elif self.GetSquare((row, column)).IsFilled():
                canDrop = False
                break
            else:
                nextSquares[i] = self.GetSquare((row, column))

        # only move the tetrad if all the target squares are valid        
        if canDrop == True:
            for i in range(4):
                self.currentTetrad.SetBlockSquare(i, nextSquares[i])
            self.eventManager.Post(TetradDroppedEvent(self.currentTetrad))

        else:
            self.currentTetrad.SetState(Tetrad.STATE_DROPPED)
            print "can't drop tetrad"

        return canDrop

    def MoveCurrentTetrad(self, direction):
        nextSquares = range(4)
        canMove = True
        row, column = (-1, -1)

        # make sure the squares the tetrad is moving to are valid and not filled        
        for i in range(4):
            row, column = self.currentTetrad.GetBlockCoordinates(i)
            if direction == DIRECTION_LEFT:
                column -= 1
            elif direction == DIRECTION_RIGHT:
                column += 1
            elif direction == DIRECTION_DOWN:
                row += 1

            if row >= Well.WELL_ROWS or column < 0 or column >= Well.WELL_COLUMNS:
                canMove = False
                break
            elif self.GetSquare((row, column)).IsFilled():
                canMove = False
                break     
            else:
                nextSquares[i] = self.GetSquare((row, column))

        # only move the tetrad if all the target squares are valid        
        if canMove == True:
            for i in range(4):
                self.currentTetrad.SetBlockSquare(i, nextSquares[i])
            self.currentTetrad.SetState(Tetrad.STATE_ACTIVE)
            self.eventManager.Post(TetradMovedEvent(self.currentTetrad))
            
            if direction != DIRECTION_DOWN:
                self.UpdateGhostTetrad()
        else:
            print "can't move tetrad"

        return canMove            


    def RotateCurrentTetrad(self, direction):
        nextSquares = range(4)
        canRotate = True
        row, column = (-1, -1)
        
        # make sure the squares the tetrad is rotating to are valid and not filled        
        for i in range(4):
            row, column = self.currentTetrad.GetRotatedBlockCoordinates(i, direction) 
            
            if row >= Well.WELL_ROWS or column < 0 or column >= Well.WELL_COLUMNS:
                canRotate = False
                break
            elif self.GetSquare((row, column)).IsFilled():
                canRotate = False
                break                
            else:
                nextSquares[i] = self.GetSquare((row, column))

        # only rotate the tetrad if all the target squares are valid        
        if canRotate == True:
            for i in range(4):
                self.currentTetrad.SetBlockSquare(i, nextSquares[i])
            self.currentTetrad.ChangeRotationState(direction)
            self.currentTetrad.SetState(Tetrad.STATE_ACTIVE)
            self.eventManager.Post(TetradRotatedEvent(self.currentTetrad))
            
            self.UpdateGhostTetrad()
        else:
            print "can't rotate tetrad"

        return canRotate


    def LockCurrentTetrad(self):
        block = None
        square = None
        row, column = (-1, -1)
        clearedRows = set()
        clearedBlocks = list()
        movedBlocks = list()
        noRowsToShift = 0
        
        # add current tetrad to stack, check for cleared rows
        for block in self.currentTetrad.blocks:
            row, column = block.GetCoordinates()
            square = block.GetSquare()
            square.SetFilled()
            self.stackedBlocks[row].append(block)
            if len(self.stackedBlocks[row]) == Well.WELL_COLUMNS:
                clearedRows.add(row)

        # if any rows were marked for clearance remove them and shift down the other rows
        if len(clearedRows) > 0:
            for i in range(max(clearedRows), 0, -1):
                
                # remove rows marked for clearance
                if clearedRows & set([i]):
                    clearedBlocks.extend(self.stackedBlocks[i])
                    for block in self.stackedBlocks[i]:
                        block.GetSquare().SetFilled(False)
                    self.stackedBlocks[i] = list()
                    noRowsToShift += 1  
                
                # if rows below have been remove shift down the row
                elif noRowsToShift > 0:
                    for block in self.stackedBlocks[i]:
                        square = block.GetSquare()
                        row, column = square.GetCoordinates()
                        square.SetFilled(False)
                        square = self.GetSquare((row + noRowsToShift, column))
                        square.SetFilled()
                        block.SetSquare(square)
                    movedBlocks.extend(self.stackedBlocks[i])
                    self.stackedBlocks[i + noRowsToShift] = self.stackedBlocks[i]
                    self.stackedBlocks[i] = list()

            self.eventManager.Post(StackUpdateEvent(clearedBlocks, movedBlocks))

        print "tetrad locked"
        self.eventManager.Post(TetradLockedEvent(self.currentTetrad))

        return True

    def GetSquare(self, (row, column)):
        return self.squares[row*Well.WELL_COLUMNS + column]

    def Notify(self, event):
        if self.currentTetrad != None:
            
            if isinstance(event, TetradMoveRequest):
                if self.currentTetrad.GetState() == Tetrad.STATE_ACTIVE or self.currentTetrad.GetState() == Tetrad.STATE_DROPPED:
                    if self.MoveCurrentTetrad(event.direction) == True:
                        self.lockTimer = 10 #successful move resets lock timer
                        
                # pressing down again locks piece
                if self.currentTetrad.GetState() == Tetrad.STATE_DROPPED and event.direction == DIRECTION_DOWN:
                        self.lockTimer = 1 
                            
            if isinstance(event, SonicDropRequest):
                if self.currentTetrad.GetState() == Tetrad.STATE_ACTIVE:
                    self.SonicDropCurrentTetrad()

            elif isinstance(event, TetradRotateRequest):
                if self.currentTetrad.GetState() == Tetrad.STATE_ACTIVE or self.currentTetrad.GetState() == Tetrad.STATE_DROPPED:
                    if self.RotateCurrentTetrad(event.direction) == True:
                        self.lockTimer = 10 #successful rotate resets lock timer

            elif isinstance(event, TickEvent):
                if self.currentTetrad.GetState() == Tetrad.STATE_ACTIVE:
                    self.dropTimer -= 1
                    if self.dropTimer == 0:               
                        self.DropCurrentTetrad()
                        self.dropTimer = 20
                        
                elif self.currentTetrad.GetState() == Tetrad.STATE_DROPPED:
                    self.lockTimer -= 1
                    if self.lockTimer == 0:
                        self.LockCurrentTetrad()
                        self.lockTimer = 10


class Square:
    """Model for a square of the well that could be filled with a block"""
    def __init__(self, eventManager, row, column):
        self.eventManager = eventManager
        #self.eventManager.RegisterListener(self)

        self.row = row
        self.column = column
        self.filled = False

    def GetCoordinates(self):
        return (self.row, self.column)

    def IsFilled(self):
        return self.filled

    def SetFilled(self, filled=True):
        self.filled = filled



class Block:
    """Model for the individual blocks that make up tetrads and the pile at the bottom."""
    
    def __init__(self, eventManager):
        self.eventManager = eventManager
        #self.eventManager.RegisterListener

        #the current square the block occupies
        self.square = None


    def GetCoordinates(self):
        if self.square == None:
            print "block has no coordinates"
            return (-1, -1)
        return self.square.GetCoordinates()

    def SetSquare(self, square):
        self.square = square

    def GetSquare(self):
        return self.square




class Tetrad:
    """Model for the tetrads that fall from the top into the pile at the bottom."""

    STATE_INACTIVE = 0
    STATE_ACTIVE = 1
    STATE_DROPPED = 2
    STATE_LOCKED = 3
    
    def __init__(self, eventManager):
        self.eventManager = eventManager
        #self.eventManager.RegisterListener(self)

        # create tetrads blocks
        self.blocks = range(4)
        for i in range(0, 4):
            self.blocks[i] = Block(eventManager)

        self.state = self.STATE_INACTIVE
        self.rotationState = 0
        
        self.colour = GREY
        self.initialBlockCoordinates = [(-1, -1), (-1, -1), (-1, -1), (-1, -1)]


    def GetBlock(self, blockIndex):
        return self.blocks[blockIndex]

    def GetInitialBlockCoordinates(self, blockIndex):
        return self.initialBlockCoordinates[blockIndex]
    
    def GetPreviewBlockCoordinates(self, blockIndex):
        row, column = self.initialBlockCoordinates[blockIndex]
        return (row - 2, column - 3)
    
    def GetColour(self):
        return self.colour


    def SetState(self, state):
        self.state = state
        
    def GetState(self):
        return self.state


    def ResetRotationState(self):
        self.rotationState = 0
        
    def ChangeRotationState(self, direction):
        if direction == DIRECTION_CW:
            self.rotationState = (self.rotationState + 1) % 4
        else:
            self.rotationState = (self.rotationState - 1) % 4
        
    def GetRotationState(self):
        return self.rotationState
    
    def SetBlockSquare(self, blockIndex, square):
        self.blocks[blockIndex].SetSquare(square)

    def GetBlockSquare(self, blockIndex):
        square = self.blocks[blockIndex].GetSquare()
        return square
    
    def ClearBlocksSquares(self):
        for block in self.blocks:
            block.SetSquare(None)

    def GetBlockCoordinates(self, blockIndex):
        return self.blocks[blockIndex].GetCoordinates()

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        return self.GetBlockCoordinates(blockIndex)

    def GetRandomTetrad(eventManager):
        randNum = random.randint(1,7)
        tetrad = None
        if randNum == 1:
            tetrad = OTetrad(eventManager)
        elif randNum == 2:
            tetrad = ITetrad(eventManager)
        elif randNum == 3:
            tetrad = TTetrad(eventManager)
        elif randNum == 4:
            tetrad = ZTetrad(eventManager)
        elif randNum == 5:
            tetrad = STetrad(eventManager)
        elif randNum == 6:
            tetrad = LTetrad(eventManager)
        elif randNum == 7:
            tetrad = JTetrad(eventManager)
        return tetrad
    GetRandomTetrad = Callable(GetRandomTetrad)



class GhostTetrad(Tetrad):
    """the ghost or shadow of the current piece"""
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = GREY
        self.visible = True
        
    def SetVisible(self, visible=True):
        self.visible = visible
        
    def IsVisible(self):
        return self.visible
        

class OTetrad(Tetrad):
    """the 'O' shaped tetrad
            block indices: |0|1|
                           |3|2|
            rotates about centre
    """
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = YELLOW
        self.initialBlockCoordinates = [(2, 4), (2, 5), (3, 5), (3, 4)]

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if direction == DIRECTION_CW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    column += 1
                elif blockIndex == 1:
                    row += 1
                elif blockIndex == 2:
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                elif blockIndex == 1:
                    column -= 1
                elif blockIndex == 2:
                    row -= 1
                elif blockIndex == 3:
                    column += 1
            elif self.rotationState == 2:
                if blockIndex == 0:
                    column -= 1
                elif blockIndex == 1:
                    row -= 1
                elif blockIndex == 2:
                    column += 1
                elif blockIndex == 3:
                    row += 1
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                elif blockIndex == 1:
                    column += 1
                elif blockIndex == 2:
                    row += 1
                elif blockIndex == 3:
                    column -= 1
        elif direction == DIRECTION_CCW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row += 1
                elif blockIndex == 1:
                    column -= 1
                elif blockIndex == 2:
                    row -= 1
                elif blockIndex == 3:
                    column += 1
            elif self.rotationState == 3:
                if blockIndex == 0:
                    column += 1
                elif blockIndex == 1:
                    row += 1
                elif blockIndex == 2:
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row -= 1
                elif blockIndex == 1:
                    column += 1
                elif blockIndex == 2:
                    row += 1
                elif blockIndex == 3:
                    column -= 1
            elif self.rotationState == 1:
                if blockIndex == 0:
                    column -= 1
                elif blockIndex == 1:
                    row -= 1
                elif blockIndex == 2:
                    column += 1
                elif blockIndex == 3:
                    row += 1
        return (row, column)


class ITetrad(Tetrad):
    """the 'I' shaped tetrad
            block indices: |0|1|2|3|
            rotates about block 2
    """    
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = RED
        self.initialBlockCoordinates = [(2, 3), (2, 4), (2, 5), (2, 6)]

    def ChangeRotationState(self, direction):
        if direction == DIRECTION_CW:
            self.rotationState = (self.rotationState + 1) % 2
        else:
            self.rotationState = (self.rotationState - 1) % 2

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if self.rotationState == 0:
            if blockIndex == 0:
                row -= 2
                column += 2
            elif blockIndex == 1:
                row -= 1
                column += 1
            elif blockIndex == 2:
                pass
            elif blockIndex == 3:
                row += 1
                column -=1
        elif self.rotationState == 1:
            if blockIndex == 0:
                row += 2
                column -= 2
            elif blockIndex == 1:
                row += 1
                column -= 1
            elif blockIndex == 2:
                pass
            elif blockIndex == 3:
                row -= 1
                column += 1
        return (row, column)


class TTetrad(Tetrad):
    """the 'T' shaped tetrad
            block indices: |0|1|2|
                             |3|
            rotates about block 1
    """    
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = CYAN
        self.initialBlockCoordinates = [(2, 3), (2, 4), (2, 5), (3,4)]

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if direction == DIRECTION_CW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
                    column -= 1
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
                    column += 1
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    row += 1
                    column += 1
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    row += 1
                    column -= 1
        elif direction == DIRECTION_CCW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
                    column += 1
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 1
                    column -= 1
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    row += 1
                    column -= 1
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    row += 1
                    column += 1
        return (row, column)


class LTetrad(Tetrad):
    """the 'L' shaped tetrad
            block indices: |0|1|2|
                           |3|
            rotates about block 1
    """
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = ORANGE
        self.initialBlockCoordinates = [(2, 3), (2, 4), (2, 5), (3,3)]

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if direction == DIRECTION_CW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 2
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    column += 2
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    row += 2
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    column -= 2
        elif direction == DIRECTION_CCW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    column += 2
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 2
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    column -= 2
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    row += 2
        return (row, column)



class JTetrad(Tetrad):
    """the 'J' shaped tetrad
            block indices: |0|1|2|
                               |3|
            rotates about block 1
    """
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = BLUE
        self.initialBlockCoordinates = [(2, 3), (2, 4), (2, 5), (3, 5)]

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if direction == DIRECTION_CW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    column -= 2
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 2
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    column += 2
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    row += 2
        elif direction == DIRECTION_CCW:
            if self.rotationState == 0:
                if blockIndex == 0:
                    row += 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column -= 1
                elif blockIndex == 3:
                    row -= 2
            elif self.rotationState == 3:
                if blockIndex == 0:
                    row -= 1
                    column += 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column -= 1
                elif blockIndex == 3:
                    column -= 2
            elif self.rotationState == 2:
                if blockIndex == 0:
                    row -= 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row += 1
                    column += 1
                elif blockIndex == 3:
                    row += 2
            elif self.rotationState == 1:
                if blockIndex == 0:
                    row += 1
                    column -= 1
                elif blockIndex == 1:
                    pass
                elif blockIndex == 2:
                    row -= 1
                    column += 1
                elif blockIndex == 3:
                    column += 2
        return (row, column)



class ZTetrad(Tetrad):
    """the 'Z' shaped tetrad
            block indices: |0|1|
                             |2|3|
            rotates about block 2
    """
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = GREEN
        self.initialBlockCoordinates = [(2, 3), (2, 4), (3, 4), (3,5)]

    def ChangeRotationState(self, direction):
        if direction == DIRECTION_CW:
            self.rotationState = (self.rotationState + 1) % 2
        else:
            self.rotationState = (self.rotationState - 1) % 2

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if self.rotationState == 0:
            if blockIndex == 0:
                column += 2
            elif blockIndex == 1:
                row += 1
                column += 1
            elif blockIndex == 2:
                pass
            elif blockIndex == 3:
                row += 1
                column -=1
        elif self.rotationState == 1:
            if blockIndex == 0:
                column -= 2
            elif blockIndex == 1:
                row -= 1
                column -= 1
            elif blockIndex == 2:
                pass
            elif blockIndex == 3:
                row -= 1
                column += 1
        return (row, column)


class STetrad(Tetrad):
    """the 'S' shaped tetrad
            block indices:   |0|1|
                           |2|3|
            rotates about block 0
    """
    def __init__(self, eventManager):
        Tetrad.__init__(self, eventManager)
        self.colour = MAGENTA
        self.initialBlockCoordinates = [(2, 4), (2, 5), (3, 3), (3,4)]

    def ChangeRotationState(self, direction):
        if direction == DIRECTION_CW:
            self.rotationState = (self.rotationState + 1) % 2
        else:
            self.rotationState = (self.rotationState - 1) % 2

    def GetRotatedBlockCoordinates(self, blockIndex, direction):
        row, column = self.GetBlockCoordinates(blockIndex)

        if self.rotationState == 0:
            if blockIndex == 0:
                pass
            elif blockIndex == 1:
                row -= 1
                column -= 1
            elif blockIndex == 2:
                column += 2
            elif blockIndex == 3:
                row -= 1
                column += 1
        elif self.rotationState == 1:
            if blockIndex == 0:
                pass
            elif blockIndex == 1:
                row += 1
                column += 1
            elif blockIndex == 2:
                column -= 2
            elif blockIndex == 3:
                row += 1
                column -= 1
        return (row, column)


def main():
    """..."""
    pygame.init()

    eventManager = EventManager()

    keyboad = KeyboardController(eventManager)
    cpuSpinner = CPUSpinnerController(eventManager)
    pygameView = PygameView(eventManager)    

    game = Game(eventManager)

    cpuSpinner.Run()


#this calls the 'main' function when this script is executed
if __name__ == '__main__': main()
