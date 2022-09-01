import re 

urls = []
youtube_url_pattern = "https://www.youtube"
youtube_url_pattern2 = "https://youtu.be"

with open("/Users/dougkim/dev/oneshot/KakaoTalkChats.txt") as kakaotext: 
    print("Opened file")
    lines = kakaotext.readlines() 
    print("read lines")
    for line in lines: 
        if youtube_url_pattern in line or youtube_url_pattern2 in line:
            print("found a link!")
            urls.append(line)

with open("/Users/dougkim/dev/oneshot/youtube_urls.txt","w") as url_text:
    for line in urls: 
        url_text.write(line)
    print("File created!")


        
        

        

