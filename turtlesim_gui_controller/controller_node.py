#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.srv import Spawn, SetPen, TeleportAbsolute
from std_srvs.srv import Empty

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterValue

import tkinter as tk
import math
import random


class TurtleController(Node):

    def __init__(self):
        super().__init__("controller_node")

        self.cmd_pub = self.create_publisher(Twist, "/turtle1/cmd_vel", 10)

        self.spawn_client = self.create_client(Spawn, "/spawn")
        self.reset_client = self.create_client(Empty, "/reset")
        self.pen_client = self.create_client(SetPen, "/turtle1/set_pen")
        self.teleport_client = self.create_client(
            TeleportAbsolute,
            "/turtle1/teleport_absolute"
        )

        self.bg_client = self.create_client(SetParameters, "/turtlesim/set_parameters")
        self.clear_client = self.create_client(Empty, "/clear")

        self.linear = 0.0
        self.angular = 0.0

        self.pen_on = True
        self.pen_width = 3
        self.current_color = (255, 255, 255)

    def publish_velocity(self):
        msg = Twist()
        msg.linear.x = self.linear
        msg.angular.z = self.angular
        self.cmd_pub.publish(msg)

    def apply_pen(self):
        req = SetPen.Request()
        r, g, b = self.current_color

        req.r = r
        req.g = g
        req.b = b
        req.width = self.pen_width
        req.off = 0 if self.pen_on else 1

        self.pen_client.call_async(req)

    def spawn_turtle(self):
        req = Spawn.Request()
        req.x = random.uniform(1.0, 10.0)
        req.y = random.uniform(1.0, 10.0)
        req.theta = random.uniform(0.0, 3.14)
        req.name = ""
        self.spawn_client.call_async(req)

    def reset_sim(self):
        self.reset_client.call_async(Empty.Request())

    def set_random_pen(self):
        self.current_color = (
            random.randint(0, 225),
            random.randint(0, 225),
            random.randint(0, 225)
        )
        self.apply_pen()

    def toggle_pen(self):
        self.pen_on = not self.pen_on
        self.apply_pen()

    def update_pen_width(self, value):
        self.pen_width = int(value)
        self.apply_pen()

    def teleport_random(self):
        req = TeleportAbsolute.Request()
        req.x = random.uniform(1.0, 10.0)
        req.y = random.uniform(1.0, 10.0)
        req.theta = random.uniform(0.0, 6.28)
        self.teleport_client.call_async(req)

    def change_background(self):
        colors = [
            (255, 255, 255),
            (0, 0, 0),
            (150, 200, 255),
            (200, 255, 200),
            (255, 255, 150),
            (255, 200, 200)
        ]

        r, g, b = random.choice(colors)

        req = SetParameters.Request()
        req.parameters = [
            Parameter(name="background_r", value=ParameterValue(type=2, integer_value=r)),
            Parameter(name="background_g", value=ParameterValue(type=2, integer_value=g)),
            Parameter(name="background_b", value=ParameterValue(type=2, integer_value=b)),
        ]

        self.bg_client.call_async(req)
        self.clear_client.call_async(Empty.Request())


def main():
    rclpy.init()
    node = TurtleController()

    root = tk.Tk()
    root.title("Turtle Dashboard")
    root.geometry("300x560")

    # -----------------------
    # JOYSTICK
    # -----------------------
    canvas = tk.Canvas(root, width=235, height=235, bg="#f5f5f5")
    canvas.pack(pady=10)

    center = 235 // 2
    radius = 95

    canvas.create_oval(center - radius, center - radius,
                       center + radius, center + radius)

    knob = canvas.create_oval(center - 20, center - 20,
                              center + 20, center + 20,
                              fill="black")

    def move_knob(event):
        dx = event.x - center
        dy = event.y - center

        dist = math.sqrt(dx**2 + dy**2)
        if dist > radius:
            dx = dx / dist * radius
            dy = dy / dist * radius

        canvas.coords(knob,
                      center + dx - 20, center + dy - 20,
                      center + dx + 20, center + dy + 20)

        node.linear = -2.0 * (dy / radius)
        node.angular = -2.0 * (dx / radius)

    def reset_knob(event):
        canvas.coords(knob, center - 20, center - 20,
                      center + 20, center + 20)
        node.linear = 0.0
        node.angular = 0.0

    canvas.bind("<B1-Motion>", move_knob)
    canvas.bind("<ButtonRelease-1>", reset_knob)

    # -----------------------
    # SPAWN + TELEPORT
    # -----------------------
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=5)

    tk.Button(btn_frame, text="Spawn",
              font=("Arial", 10, "bold"),
              width=12, command=node.spawn_turtle).grid(row=0, column=0, padx=5)

    tk.Button(btn_frame, text="Teleport",
              font=("Arial", 10, "bold"),
              width=12, command=node.teleport_random).grid(row=0, column=1, padx=5)

    # -----------------------
    # BG COLOR (MOVED UP)
    # -----------------------
    tk.Button(root, text="BG Color",
              font=("Arial", 10, "bold"),
              width=20, command=node.change_background).pack(pady=5)

    # -----------------------
    # PEN CONTROLS
    # -----------------------
    pen_frame = tk.Frame(root)
    pen_frame.pack(pady=5)

    tk.Label(pen_frame, text="- Pen Controls -",
             font=("Arial", 10, "bold")).pack()

    # COLOR ROW (MATCH RESET WIDTH)
    color_frame = tk.Frame(pen_frame)
    color_frame.pack(pady=5)

    tk.Button(color_frame, text="Color",
              font=("Arial", 10, "bold"),
              width=16, command=node.set_random_pen).pack(side="left", padx=3)

    color_box = tk.Label(color_frame,
                         width=3, height=1,
                         bg="white", relief="solid")
    color_box.pack(side="left")

    # PEN TOGGLE
    toggle_btn = tk.Button(pen_frame,
                           font=("Arial", 10, "bold"),
                           width=20)

    def update_toggle():
        if node.pen_on:
            toggle_btn.config(text="Pen ON", bg="green", fg="white")
        else:
            toggle_btn.config(text="Pen OFF", bg="red", fg="white")

    def toggle():
        node.toggle_pen()
        update_toggle()

    toggle_btn.config(command=toggle)
    toggle_btn.pack(pady=5)

    update_toggle()

    # WIDTH SLIDER
    tk.Label(pen_frame, text="Width",
             font=("Arial", 10, "bold")).pack(anchor="w")

    tk.Scale(pen_frame,
             from_=1, to=10,
             orient="horizontal",
             length=175,
             sliderlength=20,
             command=node.update_pen_width).pack()

    # RESET
    tk.Button(root, text="RESET",
              font=("Arial", 10, "bold"),
              bg="red", fg="white",
              width=20,
              command=node.reset_sim).pack(side="bottom", pady=10)

    # LOOP
    def loop():
        node.publish_velocity()
        rclpy.spin_once(node, timeout_sec=0.0)

        r, g, b = node.current_color
        color_box.config(bg=f'#{r:02x}{g:02x}{b:02x}')

        root.after(50, loop)

    loop()
    root.mainloop()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()