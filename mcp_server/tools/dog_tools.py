"""Dog control tools for the MCP server."""

from awslabs.mcp_lambda_handler import MCPLambdaHandler
from executors import robot_executor
from models import DogID


def register_dog_tools(mcp: MCPLambdaHandler):
    """Register all dog-related tools with the MCP handler."""

    # ===== BASIC MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_move_forward(dog_id: DogID) -> str:
        """Command the dog to move forward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving forward.
        """
        robot_executor.execute_dog_action(dog_id, "move_forward", {})
        return "The dog is moving forward."

    @mcp.tool()
    def dog_move_backward(dog_id: DogID) -> str:
        """Command the dog to move backward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving backward.
        """
        robot_executor.execute_dog_action(dog_id, "move_backward", {})
        return "The dog is moving backward."

    @mcp.tool()
    def dog_move_left(dog_id: DogID) -> str:
        """Command the dog to move left.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving left.
        """
        robot_executor.execute_dog_action(dog_id, "move_left", {})
        return "The dog is moving left."

    @mcp.tool()
    def dog_move_right(dog_id: DogID) -> str:
        """Command the dog to move right.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving right.
        """
        robot_executor.execute_dog_action(dog_id, "move_right", {})
        return "The dog is moving right."

    @mcp.tool()
    def dog_move_leftfront(dog_id: DogID) -> str:
        """Command the dog to move diagonally left-forward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving diagonally left-forward.
        """
        robot_executor.execute_dog_action(dog_id, "move_leftfront", {})
        return "The dog is moving diagonally left-forward."

    @mcp.tool()
    def dog_move_rightfront(dog_id: DogID) -> str:
        """Command the dog to move diagonally right-forward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving diagonally right-forward.
        """
        robot_executor.execute_dog_action(dog_id, "move_rightfront", {})
        return "The dog is moving diagonally right-forward."

    @mcp.tool()
    def dog_move_leftback(dog_id: DogID) -> str:
        """Command the dog to move diagonally left-backward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving diagonally left-backward.
        """
        robot_executor.execute_dog_action(dog_id, "move_leftback", {})
        return "The dog is moving diagonally left-backward."

    @mcp.tool()
    def dog_move_rightback(dog_id: DogID) -> str:
        """Command the dog to move diagonally right-backward.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is moving diagonally right-backward.
        """
        robot_executor.execute_dog_action(dog_id, "move_rightback", {})
        return "The dog is moving diagonally right-backward."

    # ===== POSTURE COMMANDS =====

    @mcp.tool()
    def dog_stand_up(dog_id: DogID) -> str:
        """Command the dog to stand up.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is standing up.
        """
        robot_executor.execute_dog_action(dog_id, "stand_up", {})
        return "The dog is standing up."

    @mcp.tool()
    def dog_lay_down(dog_id: DogID) -> str:
        """Command the dog to lay down.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is laying down.
        """
        robot_executor.execute_dog_action(dog_id, "lay_down", {})
        return "The dog is laying down."

    @mcp.tool()
    def dog_hop(dog_id: DogID) -> str:
        """Command the dog to hop.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is hopping.
        """
        robot_executor.execute_dog_action(dog_id, "hop", {})
        return "The dog is hopping."

    # ===== STATUS AND MODE COMMANDS =====

    @mcp.tool()
    def dog_activate(dog_id: DogID) -> str:
        """Toggle the dog's activation state.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog activation has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "activate", {})
        return "The dog activation has been toggled."

    @mcp.tool()
    def dog_enable_walking(dog_id: DogID) -> str:
        """Toggle the dog's walking mode.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog walking mode has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "walk_mode", {})
        return "The dog walking mode has been toggled."

    @mcp.tool()
    def dog_enable_dancing(dog_id: DogID) -> str:
        """Toggle the dog's dancing mode.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog dancing mode has been toggled.
        """
        robot_executor.execute_dog_action(dog_id, "dance_mode", {})
        return "The dog dancing mode has been toggled."

    @mcp.tool()
    def dog_stop(dog_id: DogID) -> str:
        """Stop all dog movement immediately.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog has stopped all movement.
        """
        robot_executor.execute_dog_action(dog_id, "stop", {})
        return "The dog has stopped all movement."

    @mcp.tool()
    def dog_stop_with_time(
        dog_id: DogID,
        time: float = 1.0,
    ) -> str:
        """Return dog to default standing position for a specified time.

        Args:
            dog_id (DogID): Dog ID
            time (float): Time to remain in default state in seconds (default: 1.0)

        Returns:
            str: The dog is in default standing position.
        """
        parameters = {
            "time": time,
        }
        robot_executor.execute_dog_action(dog_id, "stop", parameters)
        return f"The dog is in default standing position for {time} seconds."

    # ===== ADVANCED MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_circle_movement(
        dog_id: DogID, radius: float = 1.0, clockwise: bool = True
    ) -> str:
        """Make the dog move in a circle.

        Args:
            dog_id (DogID): Dog ID
            radius (float): Circle radius factor (default: 1.0)
            clockwise (bool): Direction of circle (default: True)

        Returns:
            str: The dog is moving in a circle.
        """
        parameters = {
            "radius": radius,
            "clockwise": clockwise,
        }
        robot_executor.execute_dog_action(dog_id, "circle_movement", parameters)
        direction = "clockwise" if clockwise else "counter-clockwise"
        return f"The dog is moving in a {direction} circle."

    # ===== HEAD MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_look_up(dog_id: DogID) -> str:
        """Command the dog to look up.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking up.
        """
        robot_executor.execute_dog_action(dog_id, "look_up", {})
        return "The dog is looking up."

    @mcp.tool()
    def dog_look_down(dog_id: DogID) -> str:
        """Command the dog to look down.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking down.
        """
        robot_executor.execute_dog_action(dog_id, "look_down", {})
        return "The dog is looking down."

    @mcp.tool()
    def dog_look_left(dog_id: DogID) -> str:
        """Command the dog to look left.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking left.
        """
        robot_executor.execute_dog_action(dog_id, "look_left", {})
        return "The dog is looking left."

    @mcp.tool()
    def dog_look_right(dog_id: DogID) -> str:
        """Command the dog to look right.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking right.
        """
        robot_executor.execute_dog_action(dog_id, "look_right", {})
        return "The dog is looking right."

    @mcp.tool()
    def dog_look_upperleft(dog_id: DogID) -> str:
        """Command the dog to look up and left.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking up and left.
        """
        robot_executor.execute_dog_action(dog_id, "look_upperleft", {})
        return "The dog is looking up and left."

    @mcp.tool()
    def dog_look_upperright(dog_id: DogID) -> str:
        """Command the dog to look up and right.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking up and right.
        """
        robot_executor.execute_dog_action(dog_id, "look_upperright", {})
        return "The dog is looking up and right."

    @mcp.tool()
    def dog_look_rightlower(dog_id: DogID) -> str:
        """Command the dog to look down and right.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking down and right.
        """
        robot_executor.execute_dog_action(dog_id, "look_rightlower", {})
        return "The dog is looking down and right."

    @mcp.tool()
    def dog_look_leftlower(dog_id: DogID) -> str:
        """Command the dog to look down and left.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is looking down and left.
        """
        robot_executor.execute_dog_action(dog_id, "look_leftlower", {})
        return "The dog is looking down and left."

    # ===== ADVANCED HEAD MOVEMENT WITH PARAMETERS =====

    @mcp.tool()
    def dog_head_move(
        dog_id: DogID,
        pitch_deg: float = 0.0,
        yaw_deg: float = 0.0,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Move the dog's head to specific pitch and yaw angles.

        Args:
            dog_id (DogID): Dog ID
            pitch_deg (float): Pitch angle in degrees (up/down) (default: 0.0)
            yaw_deg (float): Yaw angle in degrees (left/right) (default: 0.0)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is moving its head.
        """
        parameters = {
            "pitch_deg": pitch_deg,
            "yaw_deg": yaw_deg,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "head_move", parameters)
        return f"The dog is moving its head to pitch {pitch_deg}° and yaw {yaw_deg}°."

    # ===== BODY POSTURE COMMANDS =====

    @mcp.tool()
    def dog_body_roll(
        dog_id: DogID,
        roll_deg: float = 0.0,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Tilt the dog's body to a specific roll angle.

        Args:
            dog_id (DogID): Dog ID
            roll_deg (float): Roll angle in degrees (default: 0.0)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is tilting its body.
        """
        parameters = {
            "roll_deg": roll_deg,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "body_row", parameters)
        return f"The dog is tilting its body to {roll_deg}° roll."

    @mcp.tool()
    def dog_balance(
        dog_id: DogID,
        roll_deg: float = 0.0,
        pitch_deg: float = 0.0,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Balance the dog with specific roll and pitch angles.

        Args:
            dog_id (DogID): Dog ID
            roll_deg (float): Roll angle in degrees (default: 0.0)
            pitch_deg (float): Pitch angle in degrees (default: 0.0)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is balancing.
        """
        parameters = {
            "roll_deg": roll_deg,
            "pitch_deg": pitch_deg,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "balance", parameters)
        return f"The dog is balancing at roll {roll_deg}° and pitch {pitch_deg}°."

    # ===== GAIT AND MOVEMENT COMMANDS =====

    @mcp.tool()
    def dog_gait_uniform(
        dog_id: DogID,
        v_x: float = 0.0,
        v_y: float = 0.0,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Make the dog gait uniformly with specified velocities.

        Args:
            dog_id (DogID): Dog ID
            v_x (float): Forward/backward velocity in m/s (default: 0.0)
            v_y (float): Left/right velocity in m/s (default: 0.0)
            time_uni (float): Duration of uniform movement in seconds (default: 1.0)
            time_acc (float): Acceleration time in seconds (default: 1.0)

        Returns:
            str: The dog is gaiting uniformly.
        """
        parameters = {
            "v_x": v_x,
            "v_y": v_y,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "gait_uni", parameters)
        return f"The dog is gaiting at {v_x} m/s forward and {v_y} m/s sideways."

    # ===== HEIGHT CONTROL =====

    @mcp.tool()
    def dog_height_move(
        dog_id: DogID,
        height: float = 0.0,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Adjust the dog's height by ascending or descending.

        Args:
            dog_id (DogID): Dog ID
            height (float): Height change in meters (positive=up, negative=down) (default: 0.0)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is adjusting its height.
        """
        parameters = {
            "ht": height,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "height_move", parameters)
        direction = (
            "ascending" if height > 0 else "descending" if height < 0 else "maintaining"
        )
        return f"The dog is {direction} by {abs(height)}m."

    # ===== LEG CONTROL =====

    @mcp.tool()
    def dog_foreleg_lift(
        dog_id: DogID,
        leg_side: str = "left",
        height: float = 0.01,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Lift one of the dog's front legs.

        Args:
            dog_id (DogID): Dog ID
            leg_side (str): Which leg to lift ("left" or "right") (default: "left")
            height (float): Height to lift the leg in meters (default: 0.01)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is lifting its front leg.
        """
        parameters = {
            "leg_index": leg_side,
            "ht": height,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "foreleg_lift", parameters)
        return f"The dog is lifting its {leg_side} front leg by {height}m."

    @mcp.tool()
    def dog_backleg_lift(
        dog_id: DogID,
        leg_side: str = "left",
        height: float = 0.01,
        time_uni: float = 1.0,
        time_acc: float = 1.0,
    ) -> str:
        """Lift one of the dog's back legs.

        Args:
            dog_id (DogID): Dog ID
            leg_side (str): Which leg to lift ("left" or "right") (default: "left")
            height (float): Height to lift the leg in meters (default: 0.01)
            time_uni (float): Time to hold position in seconds (default: 1.0)
            time_acc (float): Time to reach position in seconds (default: 1.0)

        Returns:
            str: The dog is lifting its back leg.
        """
        parameters = {
            "leg_index": leg_side,
            "ht": height,
            "time_uni": time_uni,
            "time_acc": time_acc,
        }
        robot_executor.execute_dog_action(dog_id, "backleg_lift", parameters)
        return f"The dog is lifting its {leg_side} back leg by {height}m."

    # ===== ROTATION COMMANDS =====

    @mcp.tool()
    def dog_rotate(
        dog_id: DogID,
        angle: float = 1.0,
    ) -> str:
        """Rotate the dog around its body center.

        Args:
            dog_id (DogID): Dog ID
            angle (float): Rotation angle in degrees (default: 1.0)

        Returns:
            str: The dog is rotating.
        """
        parameters = {
            "angle": angle,
        }
        robot_executor.execute_dog_action(dog_id, "rotate", parameters)
        direction = "clockwise" if angle > 0 else "counter-clockwise"
        return f"The dog is rotating {direction} by {abs(angle)}°."

    # ===== SPECIAL MOVEMENTS =====

    @mcp.tool()
    def dog_bow_back(
        dog_id: DogID,
        angle: float = 15.0,
    ) -> str:
        """Make the dog bow its head and move backwards.

        Args:
            dog_id (DogID): Dog ID
            angle (float): Bow angle in degrees (default: 15.0)

        Returns:
            str: The dog is bowing and moving backwards.
        """
        parameters = {
            "angle": angle,
        }
        robot_executor.execute_dog_action(dog_id, "bowback", parameters)
        return f"The dog is bowing {angle}° and moving backwards."

    @mcp.tool()
    def dog_body_cycle(dog_id: DogID) -> str:
        """Make the dog draw a circle with its body center while maintaining orientation.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is performing a body cycle movement.
        """
        robot_executor.execute_dog_action(dog_id, "body_cycle", {})
        return "The dog is performing a circular body movement."

    @mcp.tool()
    def dog_head_ellipse(dog_id: DogID) -> str:
        """Make the dog draw an ellipse-shaped trajectory with its head.

        Args:
            dog_id (DogID): Dog ID

        Returns:
            str: The dog is performing a head ellipse movement.
        """
        robot_executor.execute_dog_action(dog_id, "head_ellipse", {})
        return "The dog is drawing an ellipse with its head movement."
