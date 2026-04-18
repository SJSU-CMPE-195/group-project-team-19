import socket, json, time

def run_test(duration_sec=60, freq_hz=20):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    end_time = time.time() + duration_sec
    count = 0
    while time.time() < end_time:
        msg = json.dumps({"j1": 90, "action": "stress_test"})
        sock.sendto(msg.encode(), ("127.0.0.1", 5005))
        count += 1
        time.sleep(1/freq_hz)
    print(f"Sent {count} packets. Check UI for drops.")

if __name__ == "__main__":
    run_test()