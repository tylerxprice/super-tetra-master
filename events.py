class Event:
    """superclass for any events that objects my generate"""
    def __init__(self):
        self.name = "Generic Event"

class TickEvent(Event):
    def __init__(self):
        self.name = "CPU Tick Event"

class QuitEvent(Event):
    def __init__(self):
        self.name = "Program Quit Event"

class GameStartRequest(Event):
    def __init__(self):
        self.name = "Game Start Request"
        
class GamePauseRequest(Event):
    def __init__(self):
        self.name = "Game Pause Request"

class GameStartedEvent(Event):
    def __init__(self, game):
        self.name = "Game Started Event"
        self.game = game
        
class TetradsCreatedEvent(Event):
    def __init__(self, tetrads):
        self.name = "Tetrads Created Event"
        self.tetrads = tetrads

class WellBuiltEvent(Event):
    def __init__(self, well):
        self.name = "Well Finished Building Event"
        self.well = well

class TetradMoveRequest(Event):
    def __init__(self, direction):
        self.name = "Tetrad Move Request"
        self.direction = direction

class TetradRotateRequest(Event):
    def __init__(self, direction):
        self.name = "Tetrad Rotate Request"
        self.direction = direction        

class TetradMovedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Tetrad Moved Event"
        self.tetrad = tetrad

class TetradRotatedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Tetrad Rotated Event"
        self.tetrad = tetrad        

class TetradAddedEvent(Event):
    def __init__(self, currentTetrad, nextTetrads):
        self.name = "Tetrad Added Event"
        self.currentTetrad = currentTetrad
        self.nextTetrads = nextTetrads

class TetradDroppedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Tetrad Dropped Event"
        self.tetrad = tetrad        

class SonicDropRequest(Event):
    def __init__(self):
        self.name = "Sonic Drop Request Event"

class SonicDropEvent(Event):
    def __init__(self, tetrad):
        self.name = "Sonic Drop Event"
        self.tetrad = tetrad

class GhostAddedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Ghost Tetrad Added Event"
        self.tetrad = tetrad

class GhostUpdatedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Ghost Tetraded Updated Event"
        self.tetrad = tetrad


class TetradLockedEvent(Event):
    def __init__(self, tetrad):
        self.name = "Tetrad Locked Event"
        self.tetrad = tetrad

class StackUpdateEvent(Event):
    def __init__(self, clearedBlocks, movedBlocks):
        self.name = "Stack Update Event"
        self.clearedBlocks = clearedBlocks
        self.movedBlocks= movedBlocks


class TetradSwapRequest(Event):
    def __init__(self):
        self.name = "Terad Swap Request"

class TetradHeldEvent(Event):
    def __init__(self, tetrad):
        self.name = "Tetrad Held Event"
        self.tetrad = tetrad
        
class TetradSwappedEvent(Event):
    def __init__(self, currentTetrad, holdTetrad):
        self.name = "Tetrad Held Event"
        self.currentTetrad = currentTetrad
        self.holdTetrad = holdTetrad

