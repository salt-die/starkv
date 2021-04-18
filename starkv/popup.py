from kivy.uix.popup import Popup
from kivy.lang import Builder
from kivy.properties import ObjectProperty


class NewGameDialogue(Popup):
    graph_canvas = ObjectProperty()

    def __init__(self, graph_canvas):
        self.graph_canvas = graph_canvas
        super().__init__()

    def accept(self):
        self.dismiss()
        self.graph_canvas.nnodes = int(self.ids['slider'].value)
        self.graph_canvas.setup_canvas()


Builder.load_string("""
<NewGameDialogue>
    slider: slider
    title: "Number of nodes: " + str(int(slider.value))
    title_align: "center"
    size_hint: .3, .3
    auto_dismiss: False

    BoxLayout:
        orientation: "vertical"

        Slider:
            id: slider
            value: 5
            min: 3
            max: 15
            step: 1

        Button:
            text: "Accept"
            on_release: root.accept()
"""
)