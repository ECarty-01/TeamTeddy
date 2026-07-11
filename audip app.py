# Import the specific function from your actual file name
from AudioAnalysizer import detect_one_note

valid_notes = ["A","A#","Ab","B","Bb","C","C#","D","Db","E","Eb","F","F#","G","G#","Gb"]

def grade_performance(music_sheet_list, user_audio):
    notes_amount = len(music_sheet_list)
    x = 0
    score = notes_amount

    while(x < notes_amount):
        music_sheet = music_sheet_list[x]
        user_plays = user_audio[x]
        x += 1
        
        # Clean up strings: upper, strip whitespace, and REMOVE the octave number if present
        # e.g., converts "C4" -> "C", "D#5" -> "D#"
        r_user_plays = user_plays.upper().strip()
        r_user_plays = ''.join([char for char in r_user_plays if not char.isdigit()])
    
        r_music_sheet = music_sheet.upper().strip()
        r_music_sheet = ''.join([char for char in r_music_sheet if not char.isdigit()])

        if(r_user_plays == r_music_sheet):
            print("Correct note!")
        else:
            print(f"Wrong Note!! Correct note was {r_music_sheet}")
            score -= 1

    print("\nCongratulations you finished the song!!\n")
    print("Your score is: ", score ,"/", notes_amount, sep="")
    percentage = (score / notes_amount) * 100
    print("A whopping ", percentage , "%", sep="")
