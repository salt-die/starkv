from pathlib import Path

from kivy.graphics.texture import Texture

def gradient(a, b):
    """Linear interpolation from color `a` to color `b`.
    """
    return (int(x * z + y * (255 - z)) for z in range(256) for x, y in zip(a, b))


UPDATE_INTERVAL = 1 / 60
RESIZE_DELAY    = .1
INIT_SCALE      = .3
INIT_OFFSET     = .5, .5
TOUCH_INTERVAL  = .4  # Number of seconds before a touch event is considered a touch move event
MIN_SCALE       = .05

HEAD_BASE         =  -0.5,   0.0,  -4.0, 1.0, -4.0, -1.0  # Triangle base points for arrow-heads of edges

# Colors
WHITE             =   1.0,   1.0,   1.0, 1.0
BACKGROUND_COLOR  =   0.0,   0.0,   0.0, 1.0

NODE_COLOR        = 0.051, 0.278, 0.631, 1.0
HIGHLIGHTED_NODE  = 0.758, 0.823,  0.92, 1.0

EDGE_COLOR        = 0.160, 0.176, 0.467, 0.8
HIGHLIGHTED_EDGE  = 0.760, 0.235, 0.239, 1.0

HEAD_COLOR        = 0.192, 0.211, 0.560, 0.96
HIGHLIGHTED_HEAD  = 0.912, 0.282, 0.287, 1.0

SELECTED_GRADIENT = Texture.create(size=(256, 1))
SELECTED_GRADIENT.blit_buffer(
    bytes(gradient(EDGE_COLOR, HIGHLIGHTED_EDGE)),
    colorfmt='rgba',
    bufferfmt='ubyte'
)

SELECTED_GRADIENT_REVERSED = Texture.create(size=(256, 1))
SELECTED_GRADIENT_REVERSED.blit_buffer(
    bytes(gradient(HIGHLIGHTED_EDGE, EDGE_COLOR)),
    colorfmt='rgba',
    bufferfmt='ubyte'
)

# Sizes
NODE_RADIUS   = 3
NODE_WIDTH    = 3

EDGE_WIDTH    = 2
EDGE_BOUNDS   = EDGE_WIDTH * 2

HEAD_SIZE     = 5  # Size of arrow heads

# Animated Node
ANIMATED_NODE_SOURCE = str(Path("starkv") / "assets" / "star.png")
ANIMATED_NODE_COLOR  = 0.760, 0.235, 0.239, 1.0
ANIMATION_WIDTH      = 50
ANIMATION_HEIGHT     = 50
ANIMATION_WIDTH_2    = 70
ANIMATION_HEIGHT_2   = 70
ROTATE_INCREMENT     = 3
SCALE_SPEED_OUT      = .75
SCALE_SPEED_IN       = .25

ANIMATED_EDGE_WIDTH  = 15
MOVE_STEPS           = 70
