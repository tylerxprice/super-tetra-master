import os, pygame

class Callable:
    """wrapper class to have static methods"""
    def __init__(self, anycallable):
        self.__call__ = anycallable    

class Utilities:
    def LoadImage(name, colorkey=None):
        fullname = os.path.join('data', name)
        try:
            image = pygame.image.load(fullname)
        except pygame.error, message:
            print 'Cannot load image:', fullname
            raise SystemExit, message
        image = image.convert()
        if colorkey is not None:
            if colorkey is -1:
                colorkey = image.get_at((0,0))
            image.set_colorkey(colorkey, RLEACCEL)
        return image, image.get_rect()
    LoadImage = Callable(LoadImage)

    def LoadSound(name):
        class NoneSound:
            def play(self): pass
        if not pygame.mixer or not pygame.mixer.get_init():
            return NoneSound()
        fullname = os.path.join('data', name)
        try:
            sound = pygame.mixer.Sound(fullname)
        except pygame.error, message:
            print 'Cannot load sound:', fullname
            raise SystemExit, message
        return sound
    LoadSound = Callable(LoadSound)


