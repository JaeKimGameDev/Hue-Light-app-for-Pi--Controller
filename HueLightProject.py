import os
from dotenv import load_dotenv
from phue import Bridge
import tkinter as tk
from tkinter import ttk, colorchooser
from ttkthemes import ThemedTk
import colorsys  # For RGB to HSV conversion

# Load environment variables
load_dotenv()
bridgeIP = os.getenv('hueBridgeIP')


class LightApp:
    def __init__(self, root):
        """Initialize the GUI and connect to the Hue Bridge"""
        self.root = root
        self.root.title("Hue Light Switch Controller")
        self.root.geometry("600x600")

        # Store Bridge object inside the class to avoid overwrites
        self.bridge = Bridge(bridgeIP)
        self.bridge.connect()

        self.lights = self.get_lights_from_hue()
        self.light_controls = {}

        # Status label
        self.status_label = ttk.Label(root, text="Hue Bridge Connected", font=("Arial", 14), foreground="green")
        self.status_label.pack(pady=10)

        # Frame for lights
        self.light_frame = ttk.Frame(root)
        self.light_frame.pack(expand=True, fill="both", padx=10, pady=10)

        self.populate_lights()

        # Refresh button
        self.refresh_button = ttk.Button(root, text="Refresh Lights", command=self.refresh_lights)
        self.refresh_button.pack(pady=10)

    def get_lights_from_hue(self):
        """ Fetch real light data from the Philips Hue Bridge. """
        lights = self.bridge.get_light_objects('id')
        light_list = []

        for light_id, light in lights.items():
            light_list.append({
                "id": int(light_id),  # Ensure ID is an integer
                "name": light.name,
                "environment": "Default",
                "state": light.on,
                "brightness": light.brightness,
                "hue": getattr(light, 'hue', 0),
                "saturation": getattr(light, 'saturation', 254)
            })

        return light_list

    def populate_lights(self):
        """ Creates light toggles, brightness sliders, and color pickers. """
        for widget in self.light_frame.winfo_children():
            widget.destroy()

        self.light_controls.clear()
        env_frames = {}

        for light in self.lights:
            env = light["environment"]

            # Create environment frame if not exists
            if env not in env_frames:
                env_label = ttk.Label(self.light_frame, text=env, font=("Arial", 12, "bold"), anchor="w")
                env_label.pack(fill="x", padx=5, pady=(5, 2))
                env_frames[env] = ttk.Frame(self.light_frame)
                env_frames[env].pack(fill="x", padx=5, pady=5)

            # Light control frame
            light_frame = ttk.Frame(env_frames[env], relief="groove", borderwidth=2)
            light_frame.pack(fill="x", pady=5, padx=5)

            # Light name
            light_label = ttk.Label(light_frame, text=light["name"], font=("Arial", 11))
            light_label.pack(side="top", anchor="w", padx=10)

            # Toggle switch
            var = tk.BooleanVar(value=light["state"])
            toggle = ttk.Checkbutton(light_frame, variable=var,
                                     command=lambda l=light, v=var: self.toggle_light(l, v))
            toggle.pack(side="left", padx=10)

            # Brightness slider
            bright_var = tk.IntVar(value=light["brightness"])
            bright_slider = ttk.Scale(
                light_frame, from_=1, to=254, variable=bright_var, orient="horizontal",
                command=lambda val, l=light, v=bright_var: self.set_brightness(l, v)
            )
            bright_slider.pack(side="left", fill="x", expand=True, padx=10)

            # Color Picker
            color_button = ttk.Button(light_frame, text="Pick Color",
                                      command=lambda l=light: self.pick_color(l))
            color_button.pack(side="right", padx=10)

            # Store references
            self.light_controls[light["id"]] = {"toggle": var, "brightness": bright_var}

    def toggle_light(self, light, var):
        """ Toggle light state and update Hue Bridge. """
        light["state"] = var.get()
        self.bridge.set_light(light["id"], "on", light["state"])
        print(f"Toggled {light['name']} to {'ON' if light['state'] else 'OFF'}")

    def set_brightness(self, light, var):
        """ Adjust brightness and update Hue Bridge. """
        brightness = int(var.get())
        self.bridge.set_light(light["id"], "bri", brightness)
        print(f"Set {light['name']} brightness to {brightness}")

    def pick_color(self, light):
        """ Open a color chooser and update Hue Bridge. """
        color = colorchooser.askcolor()[0]  # Get RGB tuple (R, G, B)
        if color:
            r, g, b = color[0] / 255, color[1] / 255, color[2] / 255  # Normalize to 0-1
            h, s, v = colorsys.rgb_to_hsv(r, g, b)

            hue_value = int(h * 65535)  # Convert hue to 0-65535
            saturation_value = int(s * 254)  # Convert saturation to 0-254

            print(f"Set {light['name']} to Hue: {hue_value}, Saturation: {saturation_value}")
            self.bridge.set_light(light["id"], {"hue": hue_value, "sat": saturation_value, "on": True})

    def refresh_lights(self):
        """ Refresh light data from Hue Bridge. """
        self.lights = self.get_lights_from_hue()
        self.populate_lights()


if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = LightApp(root)
    root.mainloop()
