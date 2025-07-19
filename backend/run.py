from app.main import app
import multiprocessing

if __name__ == "__main__":
    # Fix multiprocessing issues on macOS
    multiprocessing.set_start_method('spawn', force=True)
    app.run(host="0.0.0.0", port=5050, debug=True, use_reloader=False) 