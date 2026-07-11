
#NOTES FOR THE TEAM (SCANNER & AUDIO):
  
# 1. 'music_sheet_list' Expects a Python list of strings 
#     representing the notes from the sheet music. Example: ['C', 'E', 'G']
       
#2. 'user_audio' Expects a Python list of strings 
#   representing the notes captured live from the microphone. Example: ['C', 'F', 'G']
       
#Note formatting: Case and accidental spaces do not matter (e.g., 'c ' or 'C' are both fine), 
#as the function automatically fixes inputs using .upper().strip().
    
#Make sure both arrays match in length before passing them to this function
   
#DELETE THE TEST SIMULATION AT THE END ITS JUST SO YOU KNOW THIS FUNCTION WORKS!!!!!!!


valid_notes = ["A","A#","Ab","B","Bb","C","C#","D","Db","E","Eb","F","F#","G","G#","Gb"]

def grade_performance(music_sheet_list, user_audio):
    notes_amount = len(music_sheet_list)
    x = 0
    score = notes_amount

# en means expected note

    en = []
    print()

    while(x < notes_amount):


        music_sheet = music_sheet_list[x]
        en = []

        en.append(music_sheet)    

        user_plays = user_audio[x]
        print()

        x+=1
        
# these revamped versions of variables make it so upper and lower case doesnt matter supposedly
        r_user_plays = user_plays.upper().strip()
    
        r_music_sheet = music_sheet.upper().strip()

    
        if(r_user_plays == r_music_sheet):

            print("correct note")
            print()
        
        else:
            print("Wrong Note!!")
            print("Correct note is ", en)
            print()
            score -= 1

# final results part

    print("Congratulations you finished the song!!\n")
    print("Your score is: ", score ,"/", notes_amount, sep="")
    percentage = (score / notes_amount) * 100
    print("A whopping ", percentage , "%", sep="")

# delete this part in the actual thing its just to test how this runs
# ==========================================
# TEST SIMULATION (Using your variables)
# ==========================================
# This mimics what the scanner and audio teams will pass to your code:
mock_sheet_music = ["C", "E", "G", "C"]
mock_user_audio  = ["C", "F", "G", "c"] 

# Runs the grading program
grade_performance(mock_sheet_music, mock_user_audio)
