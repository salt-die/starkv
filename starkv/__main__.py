from kivy.app import App

from .canvas import GraphCanvas


class Starkvy(App):
    def build(self):
        return GraphCanvas()


Starkvy.run()