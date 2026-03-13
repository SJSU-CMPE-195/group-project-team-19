from nicegui import ui
import random

#Dummy Robot State
robot_pos = {
    'x': 0, 'y': 0, 'z': 0,
    'j1': 0, 'j2': 0, 'j3': 0, 'j4': 0, 'j5': 0
}
saved_points = {}

#Movement Logic 
    #pop up messages
def notify(message):
    ui.notify(message, position='bottom-right')

def update_displays():
    # updating robot position
    lbl_cart_pos.set_text(f"X: {robot_pos['x']} | Y: {robot_pos['y']} | Z: {robot_pos['z']}")
    lbl_joint_pos.set_text(f"J1: {robot_pos['j1']}° | J2: {robot_pos['j2']}° | J3: {robot_pos['j3']}° | J4: {robot_pos['j4']}° | J5: {robot_pos['j5']}°")
ui.timer(0.2, update_displays)

def jog_cartesian(axis, direction):
    # 1 for + and -1 for -
    step = step_selector.value 
    robot_pos[axis] += (direction * step)
    update_displays()
    notify(f"Jogged {axis.upper()} by {direction * step}")

def jog_joint(joint_num, direction):
    step = step_selector.value
    joint_key = f'j{joint_num}'
    robot_pos[joint_key] += (direction * step)
    update_displays()
    notify(f"Jogged J{joint_num} by {direction * step}°")

def toggle_free_drive(e):
    if e.value:
        notify('FREE DRIVE ON: Motors relaxed. Move arm manually.')
    else:
        notify('FREE DRIVE OFF: Holding position.')

def save_new_point():
    point_name = f"Point_{len(saved_points) + 1}"
    #saving real numbers instead of randoms
    real_coords = f"X:{robot_pos['x']} Y:{robot_pos['y']} Z:{robot_pos['z']}"
    saved_points[point_name] = real_coords
    notify(f'{point_name} Saved!')
    teachpoint_list.refresh()

def delete_point(name):
    if name in saved_points:
        del saved_points[name]
        notify(f'{name} Deleted!')
        teachpoint_list.refresh()

# Header
with ui.header().classes('bg-slate-900 items-center justify-between p-4'):
    ui.label('Blundr Ground Control').classes('text-2xl font-bold')
    with ui.row().classes('gap-4 font-mono'):
        ui.label('Nano [AI]: OFFLINE').classes('text-red-400 font-bold')
        ui.label('Pi [Control]: OFFLINE').classes('text-red-400 font-bold')
# Main Content
with ui.row().classes('w-full p-4 gap-4'):

    with ui.column().classes('w-full md:w-7/12 flex-grow gap-4'): 
        
        #Live Position Display Box
        with ui.card().classes('w-full bg-slate-800 border border-slate-700'):
            ui.label('Current Position').classes('text-lg font-bold text-gray-300')
            with ui.row().classes('w-full justify-between mt-2 font-mono text-xl text-green-400'):
                lbl_cart_pos = ui.label("X: 0 | Y: 0 | Z: 0")
            with ui.row().classes('w-full justify-between mt-1 font-mono text-sm text-yellow-400'):
                lbl_joint_pos = ui.label("J1: 0° | J2: 0° | J3: 0° | J4: 0° | J5: 0°")

        # Left- Nano vision
        with ui.card().classes('w-2/3'):
            ui.label('Live Camera Feed').classes('text-xl font-bold border-b w-full pb-2')
         # Actual camera stream
            ui.skeleton().classes('w-full h-96 mt-2')
    # Right - RPI manuel control
    with ui.card().classes('w-full md:w-4/12 flex-grow bg-slate-800'):
        ui.label('Robot Controls').classes('text-xl font-bold border-b border-slate-700 w-full pb-2')

         # E-Stop
        ui.button('EMERGENCY STOP', color='red', on_click=lambda: notify('E-STOP TRIGGERED!')).classes('w-full h-14 text-lg font-bold mt-2 mb-4 shadow-lg')
                             
        with ui.tabs().classes('w-full bg-slate-900 rounded-t-lg') as tabs:
            tab_jog = ui.tab('Jog & Move')
            tab_setup = ui.tab('Setup & Config')

        with ui.tab_panels(tabs, value=tab_jog).classes('w-full bg-slate-800 rounded-b-lg p-0'):
            
            # Jogging & Teachpoints
            with ui.tab_panel(tab_jog):
                
                #Free Drive Toggle
                with ui.row().classes('w-full items-center justify-between bg-slate-700 p-2 rounded mb-4 border border-slate-600'):
                    ui.label('Free Drive (Teach Mode)').classes('text-sm text-white font-bold')
                    ui.switch(on_change=toggle_free_drive)

                # Step Size Selector
                ui.label('Step Increment (mm / degrees)').classes('text-sm text-gray-400 font-bold')
                step_selector = ui.toggle([1, 10, 25, 50, 100], value=10).classes('w-full mb-4 mt-1')

                # Cartesian JOG
                ui.label('Cartesian Jog').classes('text-sm text-gray-400 font-bold')
                with ui.grid(columns=3).classes('w-full mt-2 mb-4 gap-2'):
                    with ui.button_group():
                        ui.button('X-', on_click=lambda: jog_cartesian('x', -1))
                        ui.button('X+', on_click=lambda: jog_cartesian('x', 1))
                    with ui.button_group():
                        ui.button('Y-', on_click=lambda: jog_cartesian('y', -1))
                        ui.button('Y+', on_click=lambda: jog_cartesian('y', 1))
                    with ui.button_group():
                        ui.button('Z-', on_click=lambda: jog_cartesian('z', -1))
                        ui.button('Z+', on_click=lambda: jog_cartesian('z', 1))

                # Joint JOG
                ui.label('Joint Jog').classes('text-sm text-gray-400 font-bold mt-4')
                with ui.grid(columns=2).classes('w-full mt-2 mb-4 gap-2'):
                    for joint in range(1, 6):
                        with ui.button_group():
                            ui.button(f'J{joint}-', color='secondary', on_click=lambda j=joint: jog_joint(j, -1))
                            ui.button(f'J{joint}+', color='secondary', on_click=lambda j=joint: jog_joint(j, 1))
                
                ui.separator().classes('mt-4 mb-4')

                # Dynamic Teachpoints
                ui.label('Teachpoints').classes('text-sm text-gray-400 font-bold')
                ui.button('Save Current Pose', color='amber', icon='save', on_click=save_new_point).classes('w-full mt-2 mb-4')
                
                @ui.refreshable
                def teachpoint_list():
                    if not saved_points:
                        ui.label('No points saved yet.').classes('text-gray-500 italic text-sm')
                        return
                    for name, coords in saved_points.items():
                        with ui.row().classes('w-full items-center justify-between p-2 mt-1 bg-slate-700 rounded border border-slate-600'):
                            with ui.column().classes('gap-0'):
                                ui.label(name).classes('font-bold text-sm text-white')
                                ui.label(coords).classes('text-xs text-gray-400 font-mono')
                            # The GO and DELETE buttons 
                            with ui.row().classes('gap-1'):
                                ui.button(icon='play_arrow', color='green', on_click=lambda n=name: notify(f'Moving to {n}')).props('dense size=sm')
                                ui.button(icon='delete', color='red', on_click=lambda n=name: delete_point(n)).props('dense size=sm')
                teachpoint_list()

            # Setup & Gripper
            with ui.tab_panel(tab_setup):
                
                # Init
                ui.label('Initialization').classes('text-sm text-gray-400 font-bold')
                with ui.row().classes('w-full gap-2 mt-2 mb-4'):
                    ui.button('Init All Motors', icon='power', on_click=lambda: notify('Initializing all motors...')).classes('flex-grow')
                    ui.button('Go Home', icon='home', on_click=lambda: notify('Moving to Home Position')).classes('flex-grow')
                
                ui.separator()

                # Gripper Controls
                ui.label('End Effector (Gripper)').classes('text-sm text-gray-400 font-bold mt-4')
                with ui.row().classes('w-full gap-2 mt-2'):
                    ui.button('Open', color='black', on_click=lambda: notify('Gripper Opening')).classes('flex-grow')
                    ui.button('Close', color='black', on_click=lambda: notify('Gripper Closing')).classes('flex-grow')

                # Sliders
                ui.label('Global Velocity (%)').classes('text-sm text-gray-400 font-bold mt-6')
                ui.slider(min=10, max=100, value=50, on_change=lambda e: notify(f'Velocity set to {e.value}%')).classes('mt-2')

                ui.label('Gripper Torque/Speed').classes('text-sm text-gray-400 font-bold mt-4')
                ui.slider(min=0, max=100, value=75, on_change=lambda e: notify(f'Gripper set to {e.value}')).props('color=orange').classes('mt-2')
# Start Server
ui.dark_mode().enable()
ui.run(title="Blundr GCS") #launches the web server
