import os
import time, sys
from obswebsocket import obsws, events, requests 
from pynput.keyboard import Key, Controller
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

#OBS Setup
host = "localhost"
port = 4444
obsPassword = "OBS PASSWORD HERE"

ws = obsws(host, port, obsPassword)
ws.connect()

#Keyboard
keyboard = Controller()

#Open the driver and webpage
options = Options()

#options.add_experimental_option("detach", True)

#Directory for uBlock origin, you will need to change this
uBlock = r'C:\...\ctv-video-recorder\uBlockOrigin'
options.add_argument('load-extension=' + uBlock)
options.add_argument("--start-maximized")
options.add_argument('--disable-gpu')
options.add_experimental_option("excludeSwitches",["enable-automation"])

driver = webdriver.Chrome(options=options)
driver.get("https://www.ctv.ca")
wait = WebDriverWait(driver, 30)
os.chdir(os.getcwd()+'\\videos')

#Click sign in
signIn =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='__next']/header/div/div[3]/div[2]")))
signIn.click()

#Enter provider
providerText = "cogeco"
provider =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='searchString']")))
provider.send_keys(providerText)

#Click provider
providerBtn =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='main']/div/div[2]/div/div/div/div[3]/ol/li/a/span")))
providerBtn.click()

#Log in
username =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='userName']")))
username.send_keys("USERNAME")

password = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='password']")))
password.send_keys("PASSWORD")

signIn =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='loginButton']")))
signIn.click()

#Close popup
wait.until(EC.visibility_of_element_located((By.XPATH, "//*[@id='__next']/header/div/div[2]")))
time.sleep(2)
ActionChains(driver).key_down(Keys.ESCAPE).key_up(Keys.ESCAPE).perform()

#Season number and number of episodes change this to what you want 
seasonNum  = 3
numberOfEpisodes = 13

for episodeNum in range(11,numberOfEpisodes+1):

    print(str(episodeNum) + "/" + str(numberOfEpisodes))
    #Go to shows page change the url to your shows url 
    driver.get("https://www.ctv.ca/shows/how-its-made")

    #Go to season
    if seasonNum != 1:
        dropdown = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='dropdown-basic']")))
        dropdown.click()

        season = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='episodes']/div/div[2]/div/div/button[" + str(seasonNum-1) + "]"))) 
        season.click()

    #Go to episode
    episode = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='episodes']/div/ul/li[" + str(episodeNum) + "]/div[1]/div[1]")))
    episode.click()

    #Play episode
    while True:
        try:
            playBtn = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[12]/div[1]/div/div/div[2]/div")))
            playBtn.click()
            print("Playing")

            time.sleep(1)

            #Calculate episode time in seconds
            episodeTime = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[12]/div[4]/div[2]/div[10]")))     
            episodeTimeText = episodeTime.text
            eM , es = episodeTimeText.split(':')
            episodeSeconds = (int(eM) * 60) + int(es)    

            #Adjust quality
            settings = wait.until(EC.visibility_of_element_located((By.XPATH,'//*[@id="vidi_player_instance_1"]/div[2]/div[12]/div[4]/div[2]/div[16]')))
            settings.click()
            quality = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="jw-settings-submenu-quality"]/div/button[2]')))
            quality.click()
        except:
            driver.refresh()
            print("Error - refreshing")
            continue
        break

    #Go fullscreen and move video to start
    fullscreen = wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[12]/div[4]/div[2]/div[17]")))
    fullscreen.click()
    time.sleep(5)
    ActionChains(driver).key_down('0').key_up('0').perform()

    #OBS recording
    buffered = False

    while True:
        video =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='vidi_player_instance_1']")))
        videoState = video.get_attribute("class");

        if "jw-state-buffering" in videoState:
            if not buffered:
                print("Video buffering")
                buffered = True
            continue
        else:
            if buffered:
                print("Finished buffering")
            ws.call(requests.StartRecording())
            break
    
    filename =  driver.find_element(By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[8]/div[1]").get_attribute("innerText")
    filename = filename.replace('.','').replace(':','').replace(',','').replace(' ','.') + ".1080p.CTV.WEBRip.H.265-DUCT.mp4"
    print(f"----------\nRecording: {filename}")

    #print("Fast forwarding")
    #ActionChains(driver).key_down('9').key_up('9').perform()
    #for i in range(15):
        #ActionChains(driver).key_down(Keys.ARROW_RIGHT).key_up(Keys.ARROW_RIGHT).perform()

    while True:
        try:
            autoplay = driver.find_element(By.CLASS_NAME,"dismiss-button")
        except:
            count =  driver.find_element(By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[12]/div[4]/div[2]/div[9]")
            sys.stdout.write("\r" + "Time Remaining: " + count.get_attribute("innerText"))
            sys.stdout.flush()
            continue
        break

    autoplay = wait.until(EC.visibility_of_element_located((By.CLASS_NAME,"dismiss-button")))
    video =  wait.until(EC.visibility_of_element_located((By.XPATH,"//*[@id='vidi_player_instance_1']")))

    driver.execute_script("arguments[0].setAttribute('class','jwplayer jw-reset jw-state-playing jw-stretch-uniform jw-flag-aspect-mode jw-breakpoint-6 jw-floating-dismissible bm-video-player-bm-view-pause-ads jw-flag-fullscreen jw-orientation-portrait jw-flag-user-inactive')", video)
    autoplay.click()
    driver.execute_script("arguments[0].setAttribute('class','jwplayer jw-reset jw-state-playing jw-stretch-uniform jw-flag-aspect-mode jw-breakpoint-6 jw-floating-dismissible bm-video-player-bm-view-pause-ads jw-flag-fullscreen jw-orientation-portrait jw-flag-user-inactive')", video)

    while True:
        count =  driver.find_element(By.XPATH,"//*[@id='vidi_player_instance_1']/div[2]/div[12]/div[4]/div[2]/div[9]")
        sys.stdout.write("\r" + "Time Remaining: " + count.get_attribute("innerText"))
        sys.stdout.flush()
        if count.get_attribute("innerText") == "00:00":
            print("\n----------")
            break

    ws.call(requests.StopRecording())

    #Rename file
    while True:
        try:
            os.rename("obsvideo.mp4",filename)
        except:
            continue
        break

ws.disconnect()
