import sys
import traceback

log_file = open("full_traceback.txt", "w", encoding="utf-8")
sys.stdout = log_file
sys.stderr = log_file

print("Starting generation wrapper...")
try:
    import main
    # Determine arguments
    # main.py uses argparse. We can simulate it or call functions directly.
    # Calling run_measure_gen("PSA") is easiest.
    
    print("Running measure gen...")
    main.run_measure_gen("PSA")
    print("Finished successfully.")
except Exception:
    print("\nCRASH IN WRAPPER:")
    traceback.print_exc()
finally:
    log_file.close()
