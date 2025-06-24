import openvr
import json
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from openvr_tracker_tool import *

""" VR Platform Class """
class triad_openvr():
    def __init__(self, configfile_path=None):

        # Initialize OpenVR
        self.vr = openvr.init(openvr.VRApplication_Other)
        self.vrsystem = openvr.VRSystem()

        # Initializing object to hold indexes for various tracked objects
        self.object_names = {"Tracking Reference":[],"HMD":[],"Controller":[],"Tracker":[]}
        self.devices = {}
        self.device_index_map = {}
        poses = self.vr.getDeviceToAbsoluteTrackingPose(openvr.TrackingUniverseStanding, 0,
                                                               openvr.k_unMaxTrackedDeviceCount)

        # Loading config file
        if configfile_path:
            try:
                with open(configfile_path, 'r') as json_data:
                    config = json.load(json_data)
            except EnvironmentError: # parent of IOError, OSError *and* WindowsError where available
                print('config.json not found.')
                exit(1)

            # Iterate through the pose list to find the active devices and determine their type
            for i in range(openvr.k_unMaxTrackedDeviceCount):
                if poses[i].bDeviceIsConnected:
                    device_serial = self.vr.getStringTrackedDeviceProperty(i,openvr.Prop_SerialNumber_String).decode('utf-8')
                    for device in config['devices']:
                        if device_serial == device['serial']:
                            device_name = device['name']
                            self.object_names[device['type']].append(device_name)
                            self.devices[device_name] = vr_tracked_device(self.vr,i,device['type'])
        else:
            # Iterate through the pose list to find the active devices and determine their type
            for i in range(openvr.k_unMaxTrackedDeviceCount):
                if poses[i].bDeviceIsConnected:
                    self.add_tracked_device(i)

    def __del__(self):
        openvr.shutdown()

    def get_pose(self):
        return get_pose(self.vr)

    def poll_vr_events(self):
        """
        Used to poll VR events and find any new tracked devices or ones that are no longer tracked.
        """
        event = openvr.VREvent_t()
        while self.vrsystem.pollNextEvent(event):
            if event.eventType == openvr.VREvent_TrackedDeviceActivated:
                self.add_tracked_device(event.trackedDeviceIndex)
            elif event.eventType == openvr.VREvent_TrackedDeviceDeactivated:
                #If we were already tracking this device, quit tracking it.
                if event.trackedDeviceIndex in self.device_index_map:
                    self.remove_tracked_device(event.trackedDeviceIndex)

    def add_tracked_device(self, tracked_device_index):
        i = tracked_device_index
        device_class = self.vr.getTrackedDeviceClass(i)
        if (device_class == openvr.TrackedDeviceClass_Controller):
            device_name = "controller_"+str(len(self.object_names["Controller"])+1)
            self.object_names["Controller"].append(device_name)
            self.devices[device_name] = vr_tracked_device(self.vr,i,"Controller")
            self.device_index_map[i] = device_name
        elif (device_class == openvr.TrackedDeviceClass_HMD):
            device_name = "hmd_"+str(len(self.object_names["HMD"])+1)
            self.object_names["HMD"].append(device_name)
            self.devices[device_name] = vr_tracked_device(self.vr,i,"HMD")
            self.device_index_map[i] = device_name
        elif (device_class == openvr.TrackedDeviceClass_GenericTracker):
            device_name = "tracker_"+str(len(self.object_names["Tracker"])+1)
            self.object_names["Tracker"].append(device_name)
            self.devices[device_name] = vr_tracked_device(self.vr,i,"Tracker")
            self.device_index_map[i] = device_name
        elif (device_class == openvr.TrackedDeviceClass_TrackingReference):
            device_name = "tracking_reference_"+str(len(self.object_names["Tracking Reference"])+1)
            self.object_names["Tracking Reference"].append(device_name)
            self.devices[device_name] = vr_tracking_reference(self.vr,i,"Tracking Reference")
            self.device_index_map[i] = device_name

    def remove_tracked_device(self, tracked_device_index):
        if tracked_device_index in self.device_index_map:
            device_name = self.device_index_map[tracked_device_index]
            self.object_names[self.devices[device_name].device_class].remove(device_name)
            del self.device_index_map[tracked_device_index]
            del self.devices[device_name]
        else:
            raise Exception("Tracked device index {} not valid. Not removing.".format(tracked_device_index))

    def rename_device(self,old_device_name,new_device_name):
        self.devices[new_device_name] = self.devices.pop(old_device_name)
        for i in range(len(self.object_names[self.devices[new_device_name].device_class])):
            if self.object_names[self.devices[new_device_name].device_class][i] == old_device_name:
                self.object_names[self.devices[new_device_name].device_class][i] = new_device_name

    def get_discovered_objects(self):
        text =[]
        for device_type in self.object_names:
            plural = device_type
            if len(self.object_names[device_type])!=1:
                plural+="s"
            text.append("Found "+str(len(self.object_names[device_type]))+" "+plural)
            for device in self.object_names[device_type]:
                if device_type == "Tracking Reference":
                    text.append("  "+device+" ("+self.devices[device].get_serial()+
                          ", Mode "+self.devices[device].get_model()+
                          ", "+self.devices[device].get_model()+
                          ")")
                else:
                    text.append("  "+device+" ("+self.devices[device].get_serial()+
                          ", "+self.devices[device].get_model()+")")
        return text
    
    def get_trackers(self):
        tracker_list = []
        for device in self.object_names["Tracker"]:
            tracker_list.append(self.devices[device])
        return tracker_list