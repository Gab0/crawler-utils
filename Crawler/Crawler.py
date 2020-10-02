#!/bin/python
# -*- coding: utf-8 -*-

import logging
import sys
import time
import random

from selenium import webdriver

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains

import selenium.common.exceptions
from selenium.webdriver.common.proxy import *


# import commands
import optparse
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxProfile

from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

logging.getLogger("urllib3").setLevel(logging.WARNING)

UAH = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.50 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0"
]


class Crawler:
    def __init__(self, USER_AGENT=None, PROFILE_PATH=None):
        self.startTime = time.time()

        self.USER_AGENT = USER_AGENT
        self.PROFILE_PATH = PROFILE_PATH

        from selenium.webdriver.remote.remote_connection import LOGGER
        LOGGER.setLevel(logging.WARNING)

        self.baseTimeout = 270
        file_handler = logging.FileHandler(filename='mailer.log')
        stdout_handler = logging.StreamHandler(sys.stdout)
        handlers = [file_handler, stdout_handler]

        logging.basicConfig(
            level=logging.DEBUG,
            format=
            '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
            handlers=handlers)

        self.log = logging.getLogger('LOGGER_NAME')
        self.browser = None

        self.Identifiers = {
            'xpath': By.XPATH,
            'class': By.CLASS_NAME,
            'id': By.ID
        }

        self.setupOptionParser()

        self.lastRequest = 100
        self.startingTime = time.time()

    def changeProxy(self, proxy):
        PROXY_HOST = proxy.split(':')[0]
        PROXY_PORT = proxy.split(':')[1]

        driver = self.browser

        addrProxyParams, portProxyParams = self.getProxySettings()
        driver.command_executor._commands["SET_CONTEXT"] = (
            "POST",
            "/session/$sessionId/moz/context")
        driver.execute("SET_CONTEXT", {"context": "chrome"})

        driver.execute_script("Services.prefs.setIntPref('network.proxy.type', 1)")
        for A in addrProxyParams:
            driver.execute_script("Services.prefs.setStringPref('%s', '%s')" % (
                A, PROXY_HOST))
        for P in portProxyParams:
            driver.execute_script("Services.prefs.setIntPref('%s', '%i')" % (
                P, int(PROXY_PORT)))

        driver.execute("SET_CONTEXT", {"context": "content"})

    def getProxySettings(self):
        V = ["http", "ftp", "socks", "ssl"]

        addrProxyParams = ["network.proxy.%s" % k for k in V]
        portProxyParams = ["network.proxy.%s_port" % k for k in V]

        return addrProxyParams, portProxyParams

    def getWithProxy(self, URL):
        try:
            if self.options.useProxy:
                proxyIndex = random.randrange(0, len(self.proxylist))
                PROXY = self.proxylist[proxyIndex]
                self.changeProxy(PROXY)
            else:
                PROXY = None
            self.log.debug("Getting page %s using proxy %s;" % (URL, PROXY))
        except Exception as E:
            self.log.error("Failure to create browser!")
            raise

        bannedError = "about:neterror"
        try:
            self.log.debug("Loading page %s" % URL)
            self.browser.get(URL)
            return True
        except Exception as ERROR:
            if bannedError in str(ERROR):
                print("BURN PROXY %s" % PROXY)

                # REMOVE BANNED PROXY;
                self.proxylist[proxyIndex] = None
                self.proxylist = [p for p in self.proxylist if p]
                PL = open('proxylist.txt', 'w').write('\n'.join(self.proxylist))
                return self.getWithProxy(URL)

    def setupProxy(self, proxy, profile):
        PROXY_HOST = proxy.split(':')[0]
        PROXY_PORT = proxy.split(':')[1]

        addrProxyParams, portProxyParams = self.getProxySettings()
        profile.set_preference("network.proxy.type", 1)
        for A in addrProxyParams:
            profile.set_preference(A, PROXY_HOST)
        for P in portProxyParams:
            profile.set_preference(P, int(PROXY_PORT))
        # profile.set_preference("general.useragent.override","whater_useragent")
        profile.update_preferences()

    def create_browser(self, profile=None,
                       executable=None, proxy=None, allowImages=True):

        # QUIT PREVIOUS BROWSER METHOD. IT MAY FAIL.
        if self.browser:
            self.log.debug("Dumping last browser <farewell sweet friend>.")
            try:
                self.browser.quit()
            except Exception as e:
                self.log.error("Failure to exit browser! Terminating...")
                print(e)
                try:
                    del self.browser
                except Exception as e:
                    print("No Browser do remove.")

        self.log.debug("Creating browser...")

        # CREATE CHROME BROWSER METHOD;
        if self.options.Chrome:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("excludeSwitches", ['enable-automation'])
            chrome_options.add_experimental_option("useAutomationExtension", False)

            if self.USER_AGENT:
                chrome_options.add_argument("--user-agent=%s" % self.USER_AGENT)

            if self.PROFILE_PATH:
                chrome_options.add_argument("--user-data-dir=%s" % self.PROFILE_PATH)

            if proxy:
                chrome_options.add_argument('--proxy-server=%s' % proxy)

            if not self.options.Visible:
                chrome_options.add_argument('--headless')

            # Following line launches chrome
            self.browser = webdriver.Chrome(chrome_options=chrome_options)

        elif self.options.TOR:
            pass
            # from tbselenium import tbdriver
            # self.browser = tbdriver.TorBrowserDriver('./TOR')

        # CREATE FIREFOX BROWSER METHOD;
        elif self.options.Firefox:
            # Following line launches firefox
            if profile:
                fp = FirefoxProfile(profile)
            else:
                fp = FirefoxProfile()

            forceUAH = False
            fp.set_preference("dom.disable_beforeunload", True)
            if forceUAH:
                fp.set_preference("general.useragent.override", UAH[1])
            if not allowImages:
                fp.set_preference("permissions.default.image", 2)
            if proxy:
                self.setupProxy(proxy, fp)
            self.FireFoxOptions = Options()
            if not self.options.Visible:
                self.FireFoxOptions.add_argument("-headless")

            if executable:
                Binary = FirefoxBinary(executable)
            else:
                Binary = None
            self.browser = webdriver.Firefox(firefox_binary=Binary,
                                             firefox_options=self.FireFoxOptions,
                                             firefox_profile=fp)

        # SHOW NAVIGATION HEADER;
        print(self.browser.execute_script("return navigator.userAgent;"))

        # OTHER OPTIONS
        self.browser.set_page_load_timeout(600)
        self.browser.implicitly_wait(20)
        self.log.debug("Browser created")

    def halt(self, haltTime, Verbose=True):
        if Verbose:
            self.log.debug("Halting for %f seconds." % haltTime)
        time.sleep(haltTime)

    def softInteraction(self, target, action, *args):
        time.sleep(random.random() * 3)
        self.RequestDelay()
        FAILURES = 0
        while FAILURES < 4:
            try:
                target.__getattribute__(action)(*args)
                break
            except Exception as e:
                self.log.error(e)
                time.sleep(random.random()*3)
                FAILURES += 1

        time.sleep(random.random() * 3)

    def softKeyWrite(self, target, message, delaymul=0.1, RET=False, Blank=False):
        message = list(message)

        if Blank:
            message = [
                Keys.BACK_SPACE
                for K in range(len(target.get_attribute('value')))
            ] + message

        for char in message:
            target.send_keys(char)
            time.sleep(random.random() * delaymul)

        if RET:
            target.send_keys(Keys.RETURN)

    def scrollIntoView(self, target):
        self.browser.execute_script(
            "arguments[0].scrollIntoView(true);",
            target
        )

    def RequestDelay(self):
        Wait = 5+random.random()*5
        while time.time() - self.lastRequest < Wait:
            time.sleep(1)
            print('Delay %i|%i;' % (time.time()-self.lastRequest, Wait))
        self.lastRequest = time.time()

    def mouseHover(self, target):
        A = ActionChains(self.browser)
        A.move_to_element(target).perform()

    def deleteElement(self, target):
        self.browser.execute_script(
            """
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """,
            target
        )

    def identifierTypeSelector(self, identifierType, identifier):
        def checkIfIsSeleniumObject(subject):
            if subject:
                if type(subject) != str:
                    return True
            return False

        OBJECT_A = checkIfIsSeleniumObject(identifierType)
        OBJECT_B = checkIfIsSeleniumObject(identifier)
        if OBJECT_A:
            return identifierType
        if OBJECT_B:
            return identifier

        if not identifier and '/' in identifierType:
            identifier = identifierType
            identifierType = 'xpath'

        Identifier = (self.Identifiers[identifierType.lower()], identifier)

        return Identifier

    def waitForUrlChange(self, timeout=30):
        CurrentUrl = self.browser.current_url
        WebDriverWait(self.browser, timeout).until_not(EC.url_to_be(CurrentUrl))

    def waitForElement(self, identifierType,
                       identifier=None, action='presence', timeout=30):

        Identifier = self.identifierTypeSelector(identifierType, identifier)

        Actions = {
            'presence': EC.presence_of_element_located,
            'invisibility': EC.invisibility_of_element_located,
            'clickable': EC.element_to_be_clickable,
            'visibility': EC.visibility_of_element_located
        }
        try:
            Element = WebDriverWait(self.browser, timeout).until(
                Actions[action](Identifier))
        except selenium.common.exceptions.TimeoutException as e:
            Element = None
        return Element

    def getListOfElements(self, identifierType,
                          identifier=None, parent=None):
        Identifier = self.identifierTypeSelector(identifierType, identifier)
        if not parent:
            parent = self.browser
        T = parent.find_elements(*Identifier)
        return T

    def loadListFile(self, filename):
        data = open(filename).read().split('\n')
        data = [c for c in data if c]
        data = [c for c in data if not c.startswith("#")]

        return data

    def close(self):
        print("Closing browser.")
        self.browser.close()

    def __del__(self):
        try:
            if self.browser:
                self.browser.quit()
        except Exception as e:
            pass

        print("Crawling took %f seconds" % (time.time()-self.startingTime))

    def stdInit(self):
        self.setupOptionParser()
        self.buildOptions()
        self.create_browser()

    def setupOptionParser(self):
        self.parser = optparse.OptionParser()
        self.parser.add_option(
            '-v',
            dest='Visible',
            action='store_true',
            default=False,
            help='This makes the browser visible')

        self.parser.add_option(
            '-f',
            dest='Firefox',
            action='store_true',
            default=False,
            help='This launches Firefox webdriver.')

        self.parser.add_option(
            '-c',
            dest='Chrome',
            action='store_true',
            default=True,
            help='This launches Chrome webdriver.')

        self.parser.add_option(
            '-t',
            dest='TOR',
            action='store_true',
            default=False,
            help='This launches Tor browser webdriver.')

        self.parser.add_option(
            '-d',
            dest='debugMode',
            action='store_true',
            default=False,
            help='Run on debug mode')

        self.parser.add_option(
            '-p',
            dest='useProxy',
            action='store_true',
            default=False,
            help='Use Proxy')

    def buildOptions(self):
        self.options, self.args = self.parser.parse_args()
        self.debugMode = self.options.debugMode


if __name__ == '__main__':
    C = Crawler()
    C.stdInit()
