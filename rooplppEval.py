import multiprocessing as mp
import time


# Storeはfオブジェクトを使いたい場合、{, f:{}, ...} の形でevalStatementに渡す。


def makeStore(classMap, className):

    st = {}

    if isinstance(className, list):  # Array
        if className[0][0] == 'int':
            st = [0] * int(className[0][1][0])
        else:
            st = [{}] * int(className[0][1][0])

    else:
        for f in classMap[className]['fields'].keys():

            if classMap[className]['fields'][f] == 'int':
                # 0 initialized
                st[f] = 0
            else:
                # TODO: ex) AクラスのfieldをAクラス内で宣言したら、エラーを出す。
                #          現在は無限再帰のpython側のエラーとなっている。
                # st[f] = makeStore(classMap, classMap[className]['fields'][f])
                st[f] = {}

    return st





def callOrUncall(invert, callUncall):
    if callUncall == 'call':
        if invert:
            return 'uncall'
        else:
            return 'call'
    elif callUncall == 'uncall':
        if invert:
            return 'call'
        else:
            return 'uncall'
    else:
        raise Exception("callUncall must be call or uncall")



def addSeparatedObjToStore(classMap, className, varName, globalStore):
    newObj = {}

    
    
    for f in classMap[className]['fields'].keys():
        if classMap[className]['fields'][f] == 'int':
            # 0 initialized
            newObj[f] = 0
        else:
            newObj['type'] = className
            newObj[f] = {}

    globalStore[varName] = newObj 




 
def makeSeparatedProcess(classMap,
                         ObjType,
                         varName,
                         globalStore
                         ):

    print("making Process")
    global m
    if varName == 'program':
        m = mp.Manager()
        q = m.Queue()
    else:
        q = m.Queue()


    addSeparatedObjToStore(classMap,
                           ObjType,
                           varName, 
                           globalStore)

    updateGlobalStore(globalStore, varName, '#q', q)
    p = mp.Process(target = interpreter, 
                   args=(classMap,
                         ObjType,
                         varName,
                         q,
                         globalStore))


    global ProcDict
    global ProcessObjName
    if  varName == 'program':
        ProcessObjName = 'InitialProcess'
        ProcDict =  {'program':p}
    else:
        ProcDict[varName] = p


    time.sleep(0.2)
    p.start()

    return 





def checkVarIsSeparated(globalStore, varName, localStore):
    if localStore != None:
        return False
    for v in globalStore.keys():
        if v == varName:
            return True
    return False





def checkObjIsDeletable(varList, env):
    env['type'] = 0
    env['#q'] = 0
    for k in varList :
        if  not (env[k] == {} or env[k] == 0):
            raise Exception("you can invert-new only nil-initialized object")





def checkListIsDeletable(list):
    for i in list:
        if i != 0:
            raise Exception("you can invert-new only 0-initialized array")


# this is why Here use proxy ↓
# https://stackoverflow.com/questions/26562287/value-update-in-manager-dict-not-reflected
def updateGlobalStore(globalStore, objName, varName, value):
    if isinstance(varName, list):
        proxy = globalStore[objName]
        try:
            index = int(varName[1][0])
        except:
            raise Exception('List index must be int')
        proxy[varName[0]][index] = value
        globalStore[objName] = proxy
    else:
        proxy = globalStore[objName]
        proxy[varName] = value
        globalStore[objName] = proxy





def getType(classMap, thisType, varName):
    return classMap[thisType]['fields'][varName]
    




def checkNil(object):
    if isinstance(object, int):
        return object
    if len(object) == 0:
        return {}
    elif len(object) == 1:
        if 'type' in object:
            return {}
    else:
        return object





def evalExp(thisStore, exp):
    if len(exp) == 1:  
        # [<int>] 
        if isinstance(exp[0], list):
            return thisStore[exp[0][0]][int(exp[0][1][0])]

        if exp[0].isdecimal():
            # int (exp[0] is string. turn it to int Here.)
            return int(exp[0])
        else:
            # keyがtypeだけのものも{}でreturnする必要がある。
            if exp[0] == 'nil':
                return {}
            # else exp[0] is varName
            return thisStore[exp[0]]
    else:
        if (exp[1] == '+'):
            return evalExp(thisStore, exp[0]) + evalExp(thisStore, exp[2])
        elif (exp[1] == '-'):
            return evalExp(thisStore, exp[0]) - evalExp(thisStore, exp[2])

        elif (exp[1] == '/'):
            return int(evalExp(thisStore, exp[0]) / evalExp(thisStore, exp[2]))
        elif (exp[1] == '='):

            e1 = checkNil(evalExp(thisStore, exp[0]))
            e2 = checkNil(evalExp(thisStore, exp[2]))
            return e1 == e2

        elif (exp[1] == '!='):
            e1 = checkNil(evalExp(thisStore, exp[0]))
            e2 = checkNil(evalExp(thisStore, exp[2]))
            return e1 != e2
        elif (exp[1] == '&'):
            return evalExp(thisStore, exp[0]) and evalExp(thisStore, exp[2])
        elif (exp[1] == '>'):
            return evalExp(thisStore, exp[0]) > evalExp(thisStore, exp[2])
        elif (exp[1] == '<'):
            return evalExp(thisStore, exp[0]) < evalExp(thisStore, exp[2])





def getAssignmentResult(assignment, invert, left, right):
    if (assignment == '^='):
        return left ^ right
    if invert:
        if assignment == '+=':
            return  left - right
        elif assignment == '-=':
            return left + right
    else:
        if assignment == '+=':
            return left + right
        elif assignment == '-=':
            return left - right





def evalStatement(classMap,
                  statement,
                  globalStore,
                  envObjName,
                  thisType,
                  invert,
                  localStore = None):

    if statement is None:
        return
    if (statement[0] == 'assignment'): 
        # p[0] = ['assignment', p[2], p[1], p[3]]
        # ex) x += 2+1 -> ['assignment', +=, x, 2+1] 
        if isinstance(statement[2][0], list):
            # if list Elem will be assigned
            if (statement[1] == '<=>'):
                if isinstance(statement[3][0], list):
                    # if list Elem will be assigned to list
                    pass
                else:
                    pass
            else:

                nameOfList = statement[2][0][0]
                try:
                    index = int(statement[2][0][1][0])
                except:
                    raise Exception('you must input index integer for list. not String')

                if localStore is None: 
                    result = getAssignmentResult(
                            statement[1],
                            invert,
                            globalStore[envObjName][nameOfList][index],
                            evalExp(globalStore[envObjName], statement[3])
                    )
                    updateGlobalStore(
                            globalStore, 
                            envObjName, 
                            statement[2][0], 
                            result
                    )
                else:
                    result = getAssignmentResult(statement[1],
                                             invert,
                                             localStore[envObjName][nameOfList][index],
                                             evalExp(localStore[envObjName], statement[3])
                                             )
                    localStore[envObjName][nameOfList][index] = result

        else:

            if (statement[1] == '<=>'):
                # swap
                if isinstance(statement[3][0], list):
                    # if list Elem will be assigned to var
                    pass
                else:
                    pass


            else:
                # +=, -=, ^=, !=, &=  etc...
                result = getAssignmentResult(statement[1],
                                             invert,
                                             globalStore[envObjName][statement[2][0]],
                                             evalExp(globalStore[envObjName], statement[3])
                                             )
                if localStore is None: 
                    updateGlobalStore(globalStore, 
                                      envObjName, 
                                      statement[2][0], 
                                      result
                                      )
                else:
                    localStore[statement[2][0]] = result

    elif (statement[0] == 'print'):
        pass
    elif (statement[0] == 'skip'):
        pass
    elif (statement[0] == 'new'):
        # ['new', className, varName, 'separate']
        # ['new', className, [varName]]

        if invert:
            # delete (inverted new)
            if isinstance(statement[1], list): 
                # delete list
                if localStore is None:
                    checkListIsDeletable(globalStore[envObjName][statement[2][0]])
                    updateGlobalStore(globalStore,
                                      envObjName,
                                      statement[2][0],
                                      {}
                                      )
                else:
                    checkListIsDeletable(localStore[envObjName][statement[2][0]])
                    localStore[envObjName][statement[2][0]] = {}

            else: 
                # delete object (not list).
                if localStore is None: 
                    # global Scope

                    if len(statement) == 4:
                        # delete separate

                        topLevelName = globalStore[envObjName][statement[2][0]]

                        checkObjIsDeletable(globalStore[topLevelName].keys(),
                                            globalStore[topLevelName])
                        ProcDict[topLevelName].terminate()

                        globalStore.pop(topLevelName)
                        updateGlobalStore(globalStore,
                                          envObjName,
                                          statement[2][0],
                                          {}
                                          )

                    else:
                        # delete object (not separated)
                        checkObjIsDeletable(globalStore[envObjName][statement[2][0]].keys(),
                                            globalStore[envObjName][statement[2][0]])
                        updateGlobalStore(globalStore, envObjName, statement[2][0], {})

                else:
                    # local Scope
                    if len(statement) == 4:

                        # delete separate
                        topLevelName = localStore[envObjName][statement[2][0]]

                        checkObjIsDeletable(globalStore[topLevelName].keys(),
                                            globalStore[topLevelName])
                        ProcDict[topLevelName].terminate()

                        globalStore.pop(topLevelName)
                        localStore[envObjName][statement[2][0]] = {}

                    else:
                        # delete object (not separated)
                        checkObjIsDeletable(localStore[envObjName][statement[2][0]].keys(),
                                            localStore[envObjName][statement[2][0]])
                        localStore[envObjName][statement[2][0]] = {}

        else:
            # simple new
            if isinstance(statement[1], list): 
                # new list
                if localStore == None:
                    updateGlobalStore(globalStore, envObjName, statement[2][0], makeStore(classMap, statement[1]))
                else:
                    localStore[envObjName][statement[2][0]] = makeStore(classMap, statement[1])
            else: 
                # new object
                if len(statement) == 4: 
                    # ['new', className, [varName], 'separate']


                    global ProcessRefCounter
                    global ProcessObjName

                    if ProcessRefCounter == None:
                        raise Exception("ProcessRefCounter is None")
                    if ProcessObjName == None:
                        raise Exception("ProcessObjName is None")
                    ProcessRefCounter += 1

                    varName = ProcessObjName + ':' + str(ProcessRefCounter) + '_' + statement[2][0]

                    if localStore == None:
                        updateGlobalStore(globalStore,
                                          envObjName,
                                          statement[2][0],
                                          varName)
                    else:
                        localStore[envObjName][statement[2][0]] = varName

                    global p


                    makeSeparatedProcess(classMap,
                                         statement[1],
                                         varName,
                                         globalStore)


                else:
                    # new type varName
                    if localStore == None:
                        updateGlobalStore(globalStore,
                                          envObjName,
                                          statement[2][0],
                                          makeStore(classMap, statement[1])
                                          )
                    else:
                        localStore[envObjName][statement[2][0]] = makeStore(classMap, statement[1])


    elif (statement[0] == 'delete'):
        if invert:
            pass
        else:
            pass
    elif (statement[0] == 'copy'):
        if invert:
            pass
        else:
            # TODO: typecheck
            pass

    elif (statement[0] == 'call' or statement[0] == 'uncall'):
        # ['call', 'tc', 'test', [args]]
        # ['call', 'test', [args]]

        if len(statement) == 4:  # call method of object

            callerType = classMap[thisType]['fields'][statement[1]]
            callMethodInfo = classMap[callerType]['methods'][statement[2]]
            argsInfo = callMethodInfo["args"]
            callMethodName = statement[2]
            stmts = callMethodInfo["statements"]

            if localStore == None:
                callerObjGlobalName = globalStore[envObjName][statement[1]]
            else:
                callerObjGlobalName = localStore[envObjName][statement[1]]


            if isinstance(callerObjGlobalName, str):
                callerIsSeparated = checkVarIsSeparated(globalStore, callerObjGlobalName, localStore) 
            else:
                callerIsSeparated = False

            args = statement[3]

            haveAttachedArg = True 

            for i, a in enumerate(argsInfo):
                # ex) args =  [{'name': 'a', 'type': 'int'}, {'name': 'b', 'type': 'int'}]
                if type(a['type']) is list and  a['type'][1] == 'detachable':
                    haveAttachedArg= False 
                    break

            if callerIsSeparated: 

                # you are calling method of separated object
                # push to Queue, return.
                # TODO check args is attached
                q = globalStore[callerObjGlobalName]['#q']
                time.sleep(0.1)

                callUncall = callOrUncall(invert, statement[0])

                if haveAttachedArg:
                    parent_conn, child_conn = mp.Pipe()
                    q.put([statement[2], statement[3], callUncall,
                           child_conn])
                    parent_conn.recv()
                    print('received')
                    return
                else:
                    print('hello')
                    q.put([statement[2], statement[3], callUncall])
                    return

            try:  # when caller is field
                pass
            except:  # when caller is arg or local
                pass




            if  localStore == None:
                # top-level CALL
                tmp = globalStore[envObjName]
            elif localStore != None:
                # nested Objects CALL
                tmp = localStore[envObjName]
            else:
                raise Exception(
                        "call error: caller not separated and localStore is None"
                        )

            if statement[0] == 'uncall':
                invert = not invert 

            if invert:
                stmts = reversed(stmts)

            for stmt in stmts:
                evalStatement(classMap,
                              stmt,
                              globalStore, 
                              statement[1],
                              thisType, 
                              invert,
                              tmp)

            if statement[0] == 'uncall':
                #end of uncall
                invert = not invert 

            if localStore == None :
                # update globalStore if this is top-level CALL
                globalStore[envObjName] = tmp

                


                


        else:  
            # local call
            callerType = thisType
            callMethodName = statement[1]
            callMethodInfo = classMap[callerType]['methods'][callMethodName]
            callerIsSeparated = False

            stmts = callMethodInfo["statements"]
            argsInfo = callMethodInfo["args"]


            if statement[0] == 'uncall':
                invert = not invert

            if invert:
                stmts = reversed(stmts)
            for stmt in stmts:
                evalStatement(classMap, stmt, globalStore, envObjName, thisType, invert)
                
            if statement[0] == 'uncall':
                invert = not invert

                



    elif (statement[0] == 'if'):  # statement[1:4] = [e1, s1, s2, e2]
        if invert:
            e1 = statement[4]
            e2 = statement[1]
        else:
            e1 = statement[1]
            e2 = statement[4]

        if localStore is None: 
            result_e1 = evalExp(globalStore[envObjName], e1)
        else:
            result_e1 = evalExp(localStore[envObjName], e1)
        if result_e1:
            if invert:
                statements = reversed(statement[2])
            else:
                statements = statement[2]
        else:
            if invert:
                statements = reversed(statement[3])
            else:
                statements = statement[3]

        for s in statements:
            evalStatement(classMap, 
                          s, 
                          globalStore, 
                          envObjName, 
                          thisType,
                          invert, 
                          localStore)

        if localStore is None: 
            result_e2 = evalExp(globalStore[envObjName], e2)
        else:
            result_e2 = evalExp(localStore[envObjName], e2)

        if result_e2:  # e2 e1
            return
        else:
            if invert:
                raise Exception("INVERTED: e1 is False")
            else:
                raise Exception("e2 is False")


    elif (statement[0] == 'from'):  # statement[1:4] = [e1, s1, s2, e2]
        if invert:
            e1 = statement[4]
            e2 = statement[1]
            s1 = statement[2]
            s2 = statement[3]
        else:
            e1 = statement[1]
            e2 = statement[4]
            s1 = statement[2]
            s2 = statement[3]

        if localStore is None: 
            result_e1 = evalExp(globalStore[envObjName], e1)
        else:
            result_e1 = evalExp(localStore[envObjName], e1)

        print(result_e1)

        if not result_e1:
            # assertion
            raise Exception("Loop initial Condition is False")

        # initially, e1 is true.
        # e1 -> s1 -> e2 -> s2 -> e1
        while result_e1:  # e1  e2

            for s in s1:  # s1  s1
                evalStatement(classMap, 
                              s, 
                              globalStore, 
                              envObjName, 
                              thisType,
                              invert, 
                              localStore)

            if localStore is None: 
                result_e2 = evalExp(globalStore[envObjName], e2)
            else:
                result_e2 = evalExp(localStore[envObjName], e2)

            if result_e2:  # e2 e1
                break
            else:
                if invert:
                    stmts = reversed(s2)
                else:
                    stmts = s2

                for s in reversed(s2):
                    evalStatement(classMap, 
                          s, 
                          globalStore, 
                          envObjName, 
                          thisType,
                          invert, 
                          localStore)


            if localStore is None: 
                result_e1 = evalExp(globalStore[envObjName], e1)
            else:
                result_e1 = evalExp(localStore[envObjName], e1)

            # result_e1 is while condition.
            # if result_e1 is false, break while loop.
            # but in roopl, result_e1 is true only first loop.
            # after second loop, result_e1 is false permanently.
            result_e1 = not result_e1 

            if not result_e1:
                if invert:
                    print(e1)
                    raise Exception(
                        "INVERTED : Loop initial Condition is True")
                else:
                    raise Exception("Loop initial Condition is True")

    # LOCAL:0 type:1 id:2 EQ exp:3  statements:4 DELOCAL type:5 id:6 EQ exp:7
    elif (statement[0] == 'local'):

        if invert:
            id1 = statement[6][0]
            id2 = statement[2][0]
            exp1 = statement[7]
            exp2 = statement[3]
            stmts = reversed(statement[4])
        else:
            id1 = statement[2][0]
            id2 = statement[6][0]
            exp1 = statement[3]
            exp2 = statement[7]
            stmts = statement[4]
        if statement[1] != 'int':
            pass

        for s in stmts:
            pass

        try:
            pass
        except:
            pass

            #raise Exception("delocal Error")



def interpreter(classMap, 
                className, 
                objName,
                q, 
                globalStore):

    invert = False
    print("interpreter of " + className + ":"+objName + " start")

    global ProcDict
    ProcDict = {}
    global m
    m = mp.Manager()
    global ProcessObjName
    ProcessObjName = objName
    global ProcessRefCounter 
    ProcessRefCounter = 0

    while(True):
        
        try:
            x = q.qsize()
        except:
            print('ERROR:',ProcessObjName)
            raise Exception("interpreter error")

        if q.qsize() != 0:
            # an object sent request to this Process

            # sort Request Elements
            request = q.get()
            methodName = request[0]
            args = request[1]
            callORuncall = request[2]


            if len(request) == 4:
                # attached object's call
                startStatement = [callORuncall,
                                  methodName,
                                  args ]
                evalStatement(classMap,
                          startStatement,
                          globalStore,
                          objName,
                          className,
                          invert)
                print('send')
                request[3].send('signal')

            else:
                # detachable object's call
                startStatement = [callORuncall,
                                  methodName,
                                  args]
                                  
                evalStatement(classMap,
                          startStatement,
                          globalStore,
                          objName,
                          className,
                          invert)
