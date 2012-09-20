#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import sys
import termios
import tty
import traceback


SEQ_PREFIX = '\x1b'
KEY_UP = '\x1b[A'
KEY_DOWN = '\x1b[B'
KEY_LEFT = '\x1b[D'
KEY_RIGHT = '\x1b[C'
BACKSPACE = '\x7f'

CTRL_CODES = range(1,27)
CTRL_CODES.remove( 9 )
CTRL_CODES.remove( 13 )

LONGEST_SEQUENCE = 5

CSI = '\x1B['
CSI_CUB = CSI + '%iD'
CSI_CUF = CSI + '%iC'

class console:

    PROMPT = ">>>"
    CSETTING = None

    def __init__(self):
        self._handlerMap = { '^D'     : self._Exit,
                             '\r'     : self._enter,
                             BACKSPACE: self._backspace,
                             KEY_UP   : self._key_up,
                             KEY_DOWN : self._key_down,
                             KEY_LEFT : self._key_left,
                             KEY_RIGHT: self._key_right,
                             }
        self._active = True
        self._inlist = []
        self._pos = 0


    def setRawInputMode( self, mode ):
        if mode and console.CSETTING is None:
            fd = sys.stdin.fileno()
            try:
                console.CSETTING = termios.tcgetattr( fd )
                tty.setraw( sys.stdin.fileno() )
            except Exception,e:
                traceback.print_exc()
        elif not (mode or console.CSETTING is None):
            try:
                termios.tcsetattr( sys.stdin.fileno(), termios.TCSADRAIN, console.CSETTING )
                console.CSETTING = None
            except Exception, e:
                traceback.print_exc()


    def _getch( self, buf = None ):
        """ 获取命令行字符 """
        try:
            ch = sys.stdin.read( 1 )
        except KeyboardInterrupt:
            return self._getch( buf )

        if ch == SEQ_PREFIX:
            buf = [ ch ]
            result = self._getch( buf )
        elif  buf is not None:
            # 方向键解析
            buf.append( ch )
            strval = ''.join( buf )
            posixVal = self._normalizeSequence( strval )
            if posixVal:
                return posixVal
            elif len( buf ) > LONGEST_SEQUENCE:
                return self._getch()
            else:
                return  self._getch( buf )
        elif ord( ch ) in CTRL_CODES:
            # 所有Ctrl + 字母的控制键组合，其值都是相应的字母减去64
            result = '^' + chr( ord( ch ) + 64 )
        else:
            result = ch

        return result
        

    def sh(self):
        """ main loop """
        self._showprompt()
        self.setRawInputMode(True)

        while self._active:
            try:
                c = self._getch()
                self._hander(c)
            except Exception, e:
                print e

    
    def _normalizeSequence( self, strval ):
        """ 拼接特殊命令, 如方向键等"""
        if strval in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT):
            return strval
        return None


    def _hander( self, ch ):
        if ch in self._handlerMap:
            self._handlerMap[ ch ]()
        else:
            self._printOut( ch )


    def _showprompt( self ):
        sys.stdout.write(console.PROMPT)


    def _printOut( self, ch ):
        """ 输出普通字符 """
        tail =  self._inlist[self._pos:]

        for c in ch:
            self._inlist.insert( self._pos, c )
            self._pos += 1

        sys.stdout.write( ch )
        sys.stdout.write( ''.join( tail ) )
        self.moveBack( len(tail) )

    
    def moveBack( self, l ):
        if l > 0:
            sys.stdout.write( CSI_CUB % l )

    def moveForward( self, l ):
        if l > 0:
            sys.stdout.write( CSI_CUF % l )
    
    def _enter( self ):
        """ 处理回车符号 """
        self.setRawInputMode( False )
        if len( self._inlist ) > 0:
            sys.stdout.write( '\n' + ''.join( self._inlist ) + '\n' )
        else:
            sys.stdout.write( '\n' )
        self._inlist = []
        self._pos = 0

        self._showprompt()
        self.setRawInputMode( True )


    def _Exit( self ):
        os._exit( 0 )

    def _key_up( self ):
        print 'up'

    def _key_down( self ):
        print 'down'

    def _key_left( self ):
        """ 左方向键，往回退一个字符 """
        if self._pos > 0:
            self._pos -= 1
            self.moveBack( 1 )

    def _key_right( self ):
        if self._pos < len( self._inlist ):
            self._pos += 1
            self.moveForward( 1 )

    def _backspace( self ):
        """ 回格 """
        if self._pos > 0:
            self._pos -= 1
            del self._inlist[ self._pos ]
            self.moveBack( 1 )

            self._inlist.append(' ')
            self._showTail()
            del self._inlist[-1]


    def _showTail( self ):
        toWrite = self._inlist[self._pos:]
        sys.stdout.write( ''.join( toWrite ) )
        self.moveBack( len( toWrite ) )



if __name__ == '__main__':
    c = console()
    c.sh()
