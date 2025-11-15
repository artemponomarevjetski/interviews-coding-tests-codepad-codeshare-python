"""
This code analyzes all chess endings with 4 pieces or less.
"""
import chess
import chess.pgn
import chess.svg
import os
import time
from pathlib import Path

# CairoSVG import for PNG conversion
try:
    import cairosvg
except ImportError:
    cairosvg = None

def animate_game(pgn_path, output_folder, delay=1.0):
    """
    Animates a chess game move-by-move using PGN.

    Args:
        pgn_path (str): Path to the PGN file containing the game.
        output_folder (str): Directory to save the frames (SVG and optionally PNG).
        delay (float): Delay (in seconds) between moves for animations.
    """
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    with open(pgn_path) as pgn_file:
        game = chess.pgn.read_game(pgn_file)

    if game is None:
        print("No game found in the PGN file.")
        return

    board = game.board()

    for move_number, move in enumerate(game.mainline_moves(), start=1):
        board.push(move)
        svg_path = os.path.join(output_folder, f"frame_{move_number:03d}.svg")
        with open(svg_path, "w") as svg_file:
            svg_file.write(chess.svg.board(board))
        print(f"Generated SVG: {svg_path}")

        if cairosvg:
            png_path = os.path.join(output_folder, f"frame_{move_number:03d}.png")
            cairosvg.svg2png(url=svg_path, write_to=png_path)
            print(f"Converted to PNG: {png_path}")

        time.sleep(delay)

    print(f"Animation frames saved in '{output_folder}'.")


if __name__ == "__main__":
    # Example usage
    PGN_FILE = "example_game.pgn"  
    OUTPUT_FOLDER = "animated_frames"
    DELAY = 1.0

    # Run the animation
    animate_game(PGN_FILE, OUTPUT_FOLDER, delay=DELAY)
