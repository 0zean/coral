from raylibpy import draw_circle_lines, draw_line, draw_rectangle_lines, draw_text

from utils.entity import Entity
from utils.visuals import w2s


class ESPRenderer:
    def __init__(self, screen_width: int, screen_height: int, view_matrix: tuple[float, ...]) -> None:
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.view_matrix = view_matrix

    def draw_entity(self, entity: Entity, color: tuple[int, int, int, int]) -> None:
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
            head_z += 8

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

            delta_z = abs(head_pos[1] - leg_pos[1])
            left_x = head_pos[0] - delta_z // 3.5
            right_x = head_pos[0] + delta_z // 3.5
            top_y = head_pos[1] - 12
            bottom_y = head_pos[1] + delta_z

            bone_connections = [
                (neck[0], neck[1], right_shoulder[0], right_shoulder[1]),
                (neck[0], neck[1], left_shoulder[0], left_shoulder[1]),
                (arm_left[0], arm_left[1], left_shoulder[0], left_shoulder[1]),
                (arm_right[0], arm_right[1], right_shoulder[0], right_shoulder[1]),
                (arm_right[0], arm_right[1], hand_right[0], hand_right[1]),
                (arm_left[0], arm_left[1], hand_left[0], hand_left[1]),
                (neck[0], neck[1], waist[0], waist[1]),
                (knee_right[0], knee_right[1], waist[0], waist[1]),
                (knee_left[0], knee_left[1], waist[0], waist[1]),
                (knee_left[0], knee_left[1], ankle_left[0], ankle_left[1]),
                (knee_right[0], knee_right[1], ankle_right[0], ankle_right[1]),
            ]

            # Draw Skeleton
            for conn in bone_connections:
                draw_line(int(conn[0]), int(conn[1]), int(conn[2]), int(conn[3]), color)

            # Draw Box
            draw_rectangle_lines(
                int(left_x), int(head_pos[1]), int(right_x - left_x), int(bottom_y - head_pos[1] + 7), color
            )

            # Draw Head Circle
            draw_circle_lines(int(head[0]), int(head[1]), abs(head[1] - neck[1]) * 1.125, color)

            # Draw Health Bar
            health = entity.health
            health_color = (0, 200, 0, 255) if health >= 70 else (255, 140, 0, 255) if health > 30 else (255, 0, 0, 255)
            scaled_health_pos = head_pos[1] + ((100 - int(health)) / 100.0) * delta_z
            draw_line(int(left_x - 5), int(scaled_health_pos), int(left_x - 5), int(leg_pos[1]), health_color)
            draw_text(f"HP: {health}", int(left_x), int(bottom_y), 10, (255, 255, 0, 255))

            # Name
            draw_text(entity.name, int(left_x), int(top_y), 12, (255, 255, 0, 255))
        except Exception as e:
            print(f"Error drawing entity: {e}")
