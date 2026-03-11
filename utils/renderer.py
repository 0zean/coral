from raylibpy import Color, Vector2, draw_circle_lines, draw_line, draw_rectangle_lines, draw_text, draw_text_ex

from utils.entity import Entity
from utils.visuals import w2s


class ESPRenderer:
    def __init__(self, screen_width: int, screen_height: int, view_matrix: tuple[float, ...], font: any = None) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.view_matrix = view_matrix
        self.font = font

    def draw_entity(self, entity: Entity, color: Color) -> None:
        bones = entity.bones

        def proj(bone):
            return w2s(self.view_matrix, *bones[bone], self.screen_width, self.screen_height)

        try:
            head = proj("head")
            knee_left, ankle_left = proj("knee_left"), proj("ankle_left")
            knee_right, ankle_right = proj("knee_right"), proj("ankle_right")
            neck, right_shoulder, left_shoulder = proj("neck"), proj("shoulder_right"), proj("shoulder_left")
            arm_right, hand_right = proj("arm_right"), proj("hand_right")
            arm_left, hand_left = proj("arm_left"), proj("hand_left")
            waist = proj("waist")

            head_bone = bones["head"]
            leg_bone = bones["leg"]

            head_x, head_y, head_z = bones["head"]
            head_z += 8.0

            head_pos = w2s(
                self.view_matrix,
                float(head_x),
                float(head_y),
                float(head_z),
                self.screen_width,
                self.screen_height,
            )
            leg_pos = w2s(
                self.view_matrix,
                float(head_bone[0]),
                float(head_bone[1]),
                float(leg_bone[2]),
                self.screen_width,
                self.screen_height,
            )

            # Early exit if both head and legs are off-screen, skip drawing this entity
            if head_pos == [-999, -999] and leg_pos == [-999, -999]:
                return

            bone_connections = [
                (neck, right_shoulder),
                (neck, left_shoulder),
                (arm_left, left_shoulder),
                (arm_right, right_shoulder),
                (arm_right, hand_right),
                (arm_left, hand_left),
                (neck, waist),
                (knee_right, waist),
                (knee_left, waist),
                (knee_left, ankle_left),
                (knee_right, ankle_right),
            ]

            # Collect successfully projected valid bones to determine the bounding box
            valid_y = []
            valid_x = []

            # Draw Skeleton and collect bounding coordinates
            for b1, b2 in bone_connections:
                if b1[0] != -999 and b1[1] != -999 and b2[0] != -999 and b2[1] != -999:
                    draw_line(int(b1[0]), int(b1[1]), int(b2[0]), int(b2[1]), color)
                    valid_y.extend([b1[1], b2[1]])
                    valid_x.extend([b1[0], b2[0]])

            if head[0] != -999 and head[1] != -999:
                valid_y.append(head[1])
                valid_x.append(head[0])

            # If no valid coordinates were drawn, skip drawing the box/HP entirely
            if not valid_y or not valid_x:
                return

            # Dynamic Bounding Box derived strictly from rendered bones
            min_y = min(valid_y) - 10.0  # Top buffer for head
            max_y = max(valid_y) + 5.0  # Bottom buffer for feet

            box_height = max_y - min_y
            box_width = box_height // 2  # Keeps standard bounding box proportion

            # Center box around X-center of valid points
            center_x = (min(valid_x) + max(valid_x)) / 2
            left_x = center_x - (box_width / 2)
            right_x = center_x + (box_width / 2)

            # Draw Box
            draw_rectangle_lines(int(left_x), int(min_y), int(box_width), int(box_height), color)

            # Draw Head Circle around true head bone if visible
            if head[0] != -999 and head[1] != -999 and neck[1] != -999:
                draw_circle_lines(int(head[0]), int(head[1]), abs(head[1] - neck[1]) * 1.125, color)

            # Draw Health Bar
            health = entity.health
            health_color = (
                Color(0, 200, 0, 255)
                if health >= 70.0
                else Color(255, 140, 0, 255)
                if health > 30.0
                else Color(255, 0, 0, 255)
            )
            scaled_health_pos = min_y + ((100 - int(health)) / 100.0) * box_height
            draw_line(int(left_x - 5), int(scaled_health_pos), int(left_x - 5), int(max_y), health_color)

            if self.font:
                draw_text_ex(self.font, f"HP: {health}", Vector2(left_x, max_y + 2), 12, 1, Color(255, 255, 0, 255))
                draw_text_ex(self.font, entity.name, Vector2(left_x, min_y - 12), 16, 1, Color(255, 255, 0, 255))
            else:
                draw_text(f"HP: {health}", int(left_x), int(max_y + 2), 10, Color(255, 255, 0, 255))
                draw_text(entity.name, int(left_x), int(min_y - 12), 12, Color(255, 255, 0, 255))
        except Exception as e:
            print(f"Error drawing entity: {e}")
