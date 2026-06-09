from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, List


class LaneInformation(BaseModel):
    NumberOfLanes: Literal["1", "2", "3", "4", "MultipleLanes", "NoLane"]
    LaneMarkings: Literal["LaneVisible", "LaneNotClearlyVisible", "LaneNotVisible"]
    SpecialLanes: List[Literal[
        "NoSpecialLanes", "Street Parking", "Bike Lane", "Bridge", "Center Lane",
        "Construction Barriers", "Construction Cones", "Crosswalk", "Forward Only Lane",
        "Left Turn Only Lane", "Right Turn Only Lane", "Road Work", "Roundabout",
        "Taxi and Bus Lane", "Traffic Cones Blocking Parts of the Road"
    ]]


class TrafficSigns(BaseModel):
    TrafficSignsTypes: List[Literal[
        "NoTrafficSigns", "Speed Limit", "Stop Sign", "Traffic Light", "Yield Sign",
        "Pedestrian Crossing", "Pedestrian Signal", "Pedestrian Warning", "School Zone",
        "No Parking", "Parking Sign", "No Stopping", "No U-Turn", "No Left Turn",
        "No Right Turn", "No Turn On Red", "One Way Sign", "Route Sign", "Street Sign",
        "Directional Arrow", "Do Not Enter", "Road Work", "Road Work Ahead",
        "Construction Warning", "Work Zone", "End Road Work", "Bike Lane Sign",
        "Bike Lane Ends", "Bus Lane", "Bus Stop Sign", "Railroad Crossing",
        "Share the Road", "Weight Limit", "Exit Sign", "Information Sign",
        "Electronic Sign", "Keep Right Sign", "Merge Sign", "Left Turn Only",
        "Right Turn Only", "Left Lane Must Turn Left", "Right Lane Must Turn Right",
        "Do Not Block", "Do Not Block Intersection", "Crosswalk Closed",
        "No Pedestrian Crossing", "Stop for Pedestrians", "Yield to Pedestrians",
        "Speeding Fine Doubled", "Double Fines End", "Tow Area Sign", "Loading Zone Sign",
        "Detour", "Curve", "Fallen Sign", "Not a Thru Street", "Road Closed",
        "Traffic Light Warning Sign", "Two-Way Traffic", "Do Not Stop on Tracks"
    ]]
    TrafficSignsVisibility: Literal["SignVisible", "SignNotClearlyVisible", "SignNotVisible"]


class Vehicles(BaseModel):
    TotalNumber: Literal["NoVehicle", "One", "Few", "MultipleVehicles"]
    VehicleTypes: List[Literal[
        "Cars", "Sedan", "Compact Car", "Coupe", "Convertible", "Hatchback", "Sports Car",
        "SUV", "Crossover", "Jeep", "Pickup Truck", "Van", "Minivan", "RV",
        "Truck", "Box Truck", "Delivery Truck", "Commercial Delivery Truck", "Utility Truck",
        "Commercial Vehicle", "Commerical Truck", "Armored Truck", "Cement Mixer Truck",
        "Semi-Trailer Truck", "Bus", "Shuttle Bus", "Trolley", "Taxi", "Police Car",
        "Ambulance", "Service Vehicle", "Construction Vehicles", "Forklift",
        "Motorcycle", "Containers"
    ]]
    InMotion: List[Literal["True", "False"]]
    States: List[Literal[
        "Parked", "In Motion", "Stopped", "Stopped at Intersection",
        "Stopped at Traffic Light", "In Queue", "Merging", "Turning", "Turning Left",
        "Turning Right", "Crossing Intersection", "Exiting Intersection", "Slowing Down",
        "Waiting", "Waiting to Turn", "Waiting to Turn Left", "Waiting to Turn Right",
        "Blocking Parts of the Road", "Door Open", "Loading", "Picking up a Passenger",
        "Passenger Exiting", "Interacting with Driver", "Performing Roadwork",
        "Utility Work", "Violate Traffic Rules"
    ]]


class Visibility(BaseModel):
    General: Literal["Good", "Limited", "Reduced"]
    SpecificImpairments: List[Literal[
        "NoImpairments", "Shadows", "Camera Glare", "Obstructed",
        "Obstructed by Rain", "Reflections"
    ]]


class EgoVehicle(BaseModel):
    Direction: Literal[
        "EgoForward", "EgoMaking a Left Turn", "EgoMaking a Right Turn",
        "EgoApproaching Intersection", "EgoApproaching Roundabout",
        "EgoEntering Roundabout", "EgoExiting Roundabout", "EgoMerging",
        "EgoParked", "EgoStopped", "EgoStopped at Intersection", "EgoStopped at Stop Sign"
    ]
    Maneuver: Literal[
        "EgoMoving", "EgoSlowing Down", "EgoTurning Left", "EgoTurning Right",
        "EgoStopped in Parking Space", "EgoFollowing", "EgoFullStopped", "EgoIn Queue",
        "EgoMerging", "EgoMerging Left", "EgoOvertaking", "EgoOvertaking on Opposing Lane",
        "EgoProceeding through Intersection", "EgoWaiting", "EgoYielding"
    ]


class ModelOutput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    Scene: Literal[
        "Urban", "Suburban", "Commercial", "Industrial",
        "Intersection", "Parking Area", "Construction"
    ]
    TimeOfDay: Literal["Daytime", "Dusk/Dawn"]
    Weather: Literal["Clear", "Sunny", "Cloudy", "Partly Cloudy", "Overcast", "Rainy"]
    RoadConditions: Literal["Dry", "Wet"]
    LaneInformation: LaneInformation
    TrafficSigns: TrafficSigns
    Vehicles: Vehicles
    Pedestrians: List[Literal[
        "NoPed", "Crossing Street", "Visible on Sidewalk",
        "MultiplePed", "Interacting with Vehicle", "Wheelchair on the Street"
    ]]
    Directionality: Literal[
        "One-Way", "Two-Way", "Divided",
        "Multi-directional with median", "Roundabout", "Unknown"
    ]
    Visibility: Visibility
    ego_vehicle: EgoVehicle = Field(alias="Ego-Vehicle")
    CameraCondition: Literal["Clear", "Dirty", "Glare", "RainOnLens"]
    Severity: int = Field(ge=1, le=5)
