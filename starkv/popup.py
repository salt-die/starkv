from kivy.uix.popup import Popup
from kivy.lang import Builder


class NewGameDialogue(Popup):
    ...


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
            on_release: root.dismiss()
"""
)