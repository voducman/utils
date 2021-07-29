import os

if __name__ == "__main__":
    file = "./video-statictis.txt"
    minutes = 0
    seconds = 0
    with open(file, "r") as f:
        for line in f.readlines():
            time_splits = line.strip().split(",")[1:]
            for i, tick in enumerate(time_splits):
                if i % 2 != 0: continue 
                m_1, s_1 = tick.split(".")
                m_2, s_2 = time_splits[i+1].split(".")
                delta_minute = int(m_2) - int(m_1)
                minutes += delta_minute -1 if delta_minute > 1 else 0
                seconds += 60 - int(s_1) + int(s_2) if delta_minute >= 1 else int(s_2) - int(s_1)
    
    offset = seconds // 60
    minutes += offset
    seconds = seconds % 60
    print("Time counts: {} minutes, {} seconds.".format(minutes, seconds)) 
