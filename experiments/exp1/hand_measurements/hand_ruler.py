import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, RadioButtons
from enum import Enum
import os

class Mode(Enum):
    CALIBRATE = 0
    MEASURE = 1

class HandRuler:
    def __init__(self, argv):
        print(argv['exp_id'])
        self.image_dir = f"./experiments/{argv['exp_id']}/hand_measurements/{argv['subject_id']}"
        self.image_path = os.path.join(self.image_dir, f"hand.jpg")
        self.image = cv2.imread(self.image_path)
        if self.image is None:
            raise ValueError(f"Could not load image at {self.image_path}")
        
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        
        # State variables
        self.bones_list = ["index_00","index_01","index_02","index_03",
                            "thumb_01","thumb_02","thumb_03",
                            "ring_00","ring_01","ring_02","ring_03",
                            "pinky_00","pinky_01","pinky_02","pinky_03",
                            "middle_00","middle_01","middle_02","middle_03",
                            "thumb_end","index_end","middle_end","ring_end","pinky_end"]
        
        self.side = argv['side']
        self.mode = Mode.CALIBRATE
        self.calibration_points = []
        self.measurement_points = []
        self.current_bone = []
        self.bones = []
        self.bone_names = []
        self.checker_size_cm = argv['checker_size']  # Default checker size in cm
        self.scale_factor = None  # Pixels per cm
        
        # Initialize the plot
        self.fig, self.ax = plt.subplots(figsize=(12, 10))
        self.ax.set_title('Hand Measurement Tool - CALIBRATION MODE\nSelect two corners of a checker to calibrate')
        self.ax.imshow(self.image)
        
        # Add a small legend showing the measurement order
        legend_text = "Measurement order:\n" + "\n".join([f"{i+1}. {bone}" for i, bone in enumerate(self.bones_list[:5])])
        legend_text += "\n..."
        self.ax.text(0.05, 0.05, legend_text, transform=self.ax.transAxes,
                    fontsize=8, verticalalignment='bottom',
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        
        # Add control buttons
        self.fig.subplots_adjust(bottom=0.15)
        
        # Calibration input
        axbox = plt.axes([0.25, 0.05, 0.15, 0.05])
        self.checker_input = plt.text(0.25, 0.05, f'Checker Size (cm): {self.checker_size_cm}')
        
        # Mode selection
        rax = plt.axes([0.05, 0.05, 0.15, 0.1])
        self.radio = RadioButtons(rax, ['Calibrate', 'Measure'])
        self.radio.on_clicked(self.set_mode)
        
        # Button to finish current bone
        bax_done = plt.axes([0.45, 0.05, 0.15, 0.05])
        self.btn_done = Button(bax_done, 'Finish Bone')
        self.btn_done.on_clicked(self.finish_bone)
        
        # Button to save results
        bax_save = plt.axes([0.65, 0.05, 0.15, 0.05])
        self.btn_save = Button(bax_save, 'Save Results')
        self.btn_save.on_clicked(self.save_results)
        
        # Connect the click event
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        
        # Set up text for displaying bone lengths
        self.length_text = self.ax.text(0.05, 0.95, "", transform=self.ax.transAxes, 
                                       fontsize=10, verticalalignment='top', 
                                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
        self.update_length_text()
    
    def set_mode(self, label):
        if label == 'Calibrate':
            self.mode = Mode.CALIBRATE
            self.calibration_points = []
            self.ax.set_title('CALIBRATION MODE - Select two corners of a checker to calibrate')
        else:
            if self.scale_factor is None:
                print("Please complete calibration first!")
                self.radio.set_active(0)
                return
                
            self.mode = Mode.MEASURE
            self.ax.set_title('MEASUREMENT MODE - Click to mark bone joints')
        
        self.fig.canvas.draw_idle()
    
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        x, y = event.xdata, event.ydata
        
        if self.mode == Mode.CALIBRATE:
            self.calibration_points.append((x, y))
            self.ax.plot(x, y, 'ro', markersize=5)
            
            if len(self.calibration_points) == 2:
                # Calculate the distance and scale
                p1, p2 = self.calibration_points
                pixel_dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                self.scale_factor = pixel_dist / self.checker_size_cm
                print(f"Calibration complete: {self.scale_factor:.2f} pixels per cm")
                
                # Draw the calibration line
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'r-', linewidth=2)
                self.ax.text((p1[0] + p2[0])/2, (p1[1] + p2[1])/2, 
                           f"{self.checker_size_cm} cm", 
                           color='white', fontweight='bold', 
                           bbox=dict(facecolor='red', alpha=0.5))
                
                # Switch to measurement mode
                self.mode = Mode.MEASURE
                self.radio.set_active(1)
                self.ax.set_title('MEASUREMENT MODE - Click to mark bone joints')
        
        elif self.mode == Mode.MEASURE:
            self.current_bone.append((x, y))
            
            # Draw the point
            self.ax.plot(x, y, 'go', markersize=5)
            
            # If we have at least two points, draw the line segment
            if len(self.current_bone) >= 2:
                p1, p2 = self.current_bone[-2], self.current_bone[-1]
                self.ax.plot([p1[0], p2[0]], [p1[1], p2[1]], 'g-', linewidth=2)
        
        self.fig.canvas.draw_idle()
    
    def finish_bone(self, event):
        if len(self.current_bone) < 2:
            print("Need at least 2 points to define a bone!")
            return
        
        # Calculate the bone length
        total_length_px = 0
        for i in range(1, len(self.current_bone)):
            p1, p2 = self.current_bone[i-1], self.current_bone[i]
            segment_length_px = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_length_px += segment_length_px
        
        # Convert to cm using the scale factor
        if self.scale_factor:
            length_cm = total_length_px / self.scale_factor
            print(f"Bone length: {length_cm:.2f} cm")
        else:
            length_cm = None
            print("Warning: No calibration. Cannot convert to cm.")
        
        # Store the bone data
        self.bones.append({
            'points': self.current_bone.copy(),
            'length_px': total_length_px,
            'length_cm': length_cm,
            'name': f"Bone {len(self.bones) + 1}"
        })
        
        # Reset for next bone
        self.current_bone = []
        self.name_bone()
        
        # Update the displayed bone lengths
        self.update_length_text()
    
    def name_bone(self):
        if not self.bones:
            print("No bones to name!")
            return
        
        # Instead of manual input, offer selection from the predefined list
        if len(self.bone_names) < len(self.bones_list):
            # Get the next bone name from the list
            next_bone = self.bones_list[len(self.bone_names)]
            self.bones[-1]['name'] = next_bone
            self.bone_names.append(next_bone)
            print(f"Named as: {next_bone}")
            
            # Show next bone to measure
            if len(self.bone_names) < len(self.bones_list):
                next_up = self.bones_list[len(self.bone_names)]
                self.ax.set_title(f'MEASUREMENT MODE - Next bone: {next_up}')
            else:
                self.ax.set_title('MEASUREMENT MODE - All bones in list measured!')
        else:
            print("All predefined bones have been named. Using custom name.")
            name = input(f"Enter custom name for Bone {len(self.bones)}: ")
            if name:
                self.bones[-1]['name'] = name
                self.bone_names.append(name)
        
        self.update_length_text()
        self.fig.canvas.draw_idle()
        
    def update_length_text(self):
        if not self.bones:
            progress_info = f"Progress: 0/{len(self.bones_list)} bones measured"
            self.length_text.set_text(f"No bones measured yet.\n{progress_info}")
            return
            
        text = "Bone Measurements:\n"
        for i, bone in enumerate(self.bones):
            if bone.get('length_cm') is not None:
                text += f"{bone['name']}: {bone['length_cm']:.4f} cm\n"
            else:
                text += f"{bone['name']}: {bone['length_px']:.4f} px (not calibrated)\n"
        
        # Add progress information
        progress_info = f"Progress: {len(self.bone_names)}/{len(self.bones_list)} bones measured"
        text += f"\n{progress_info}"
        
        # Add next bone to measure
        if len(self.bone_names) < len(self.bones_list):
            text += f"\nNext: {self.bones_list[len(self.bone_names)]}"
        
        self.length_text.set_text(text)
    
    def save_results(self, event):
        # Create a result summary
        results = {
            'image_path': self.image_path,
            'checker_size_cm': self.checker_size_cm,
            'scale_factor': self.scale_factor,
            'bones': []
        }
        
        for bone in self.bones:
            results['bones'].append({
                'name': bone['name'],
                'length_cm': bone.get('length_cm'),
                'length_px': bone['length_px'],
                'points': [(int(x), int(y)) for x, y in bone['points']]
            })
        
        # Save as text file
        output_path = os.path.join(self.image_dir, f'{self.side}.txt')
        with open(output_path, 'w') as f:
            f.write(f"Image: {self.image_path}\n")
            f.write(f"Checker size: {self.checker_size_cm} cm\n")
            f.write(f"Scale factor: {self.scale_factor:.4f} pixels per cm\n\n")
            f.write("Bone measurements:\n")
            
            for bone in self.bones:
                if bone.get('length_cm') is not None:
                    f.write(f"{bone['name']},{bone['length_cm']:.4f}\n")
                else:
                    f.write(f"{bone['name']},{bone['length_px']:.4f} px (not calibrated)\n")
        
        print(f"Results saved to {output_path}")
        
        # Also create an annotated image
        output_img_path = self.image_path.rsplit('.', 1)[0] + '_annotated.png'
        self.fig.savefig(output_img_path, dpi=300, bbox_inches='tight')
        print(f"Annotated image saved to {output_img_path}")

if __name__ == "__main__":
    import json
    
    argv ={"exp_id":"exp1",
           "subject_id":"sub2",
           "side":"left",
           "checker_size":5.0} # Default checker size in cm    
    ruler = HandRuler(argv)
    plt.show()