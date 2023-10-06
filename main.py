import numpy as np


def read_patterns(filePath):
    """
    从文件中读入模式集
    :param filePath: 文件路径
    :return: 模式集
    """
    patternArray = []
    with open(filePath, 'r') as f:
        for line in f.readlines():
            patternArray.append(line.strip('\n'))
    return patternArray


def read_text(textPath):
    """
    从文件中读入待检测文本
    :param textPath: 文件路径
    :return: 待检测文本
    """
    text = ""
    with open(textPath, 'r') as f:
        for line in f.readlines():
            text = text + line.strip('\n')
    return text.replace(" ", "")


def max_len(patternArray):
    """
    计算字符集中最长字符串长度
    :param patternArray: 模式集
    :return: 最长字符串长度
    """
    maxLen = len(patternArray[0])
    for pattern in patternArray:
        if maxLen < len(pattern):
            maxLen = len(pattern)
    return maxLen


def cal_state_number(patternArray):
    """
    计算自动机状态数
    :param patternArray: 模式集
    :return: 状态数
    """
    stateNum = 0
    for pattern in patternArray:
        stateNum += len(pattern)
    return stateNum + 1


def query_next_index(nextArray, queryState):
    """
    查找 next 数组中指定状态的索引值
    :param nextArray: next 表
    :param queryState: 查询目标状态值
    :return: 索引值
    """
    arrayLen = len(nextArray)
    for i in range(arrayLen):
        if queryState == nextArray[i]:
            return i


def query_children(checkArray, queryState):
    """
    查询目标状态的子结点
    :param checkArray: check 表
    :param queryState: 待查询状态
    :return: 子结点集合
    """
    childrenList = []
    arraySize = len(checkArray)
    for i in range(arraySize):
        if checkArray[i] == queryState:
            childrenList.append(i)
    return childrenList


def distribute_next_value(nextArray):
    """
    为当前字符分配 next 空间，即返回当前数组除首位之外的第一个零值的下标
    :param nextArray: next 表
    :return: 下标
    """
    nextLen = len(nextArray)
    for i in range(1, nextLen):
        if nextArray[i] == 0:
            return i


def pre_process(patternArray):
    """
    根据模式集计算 next, base, check 表, state 表, 输出集
    :param patternArray: 模式集
    :return: next, base, check 表, state 表, 输出集
    """
    # 给定 next, base, check 表的大小
    patternArray = sorted(patternArray)  # 按照字典序排序字符集
    maxLen = max_len(patternArray) + 1  # 模式集最长字符的长度 （+1是因为第一个）
    arrayLen = len(patternArray)  # 模式集字符的个数
    maxNextLen = cal_state_number(patternArray) + 26
    maxBaseLen = cal_state_number(patternArray)

    nextArray = np.zeros(maxNextLen, dtype=int)     # 默认转移状态为 0
    baseArray = np.zeros(maxBaseLen, dtype=int)
    checkArray = np.array([-1 for _ in range(maxBaseLen)])
    stateArray = np.array(['' for _ in range(maxBaseLen)])    # 记录状态对应的字符
    fatherArray = np.zeros(len(patternArray), dtype=int)  # 记录后一层的父结点状态值

    outputArray = {}  # 输出集

    character = ""  # 记录上一个字符，用于判断是否需要新状态来存储当前字符
    state = 0  # 记录当前状态值

    # 按照字符所在层数，遍历模式集
    for i in range(maxLen):
        for j in range(arrayLen):
            father_state = fatherArray[j]
            if i >= len(patternArray[j]):
                outputArray[father_state] = [patternArray[j]]
                continue

            newChar = patternArray[j][i]
            # 判断当前字符是否变化或层数发生变化，如果字符变化，状态值加一
            if newChar != character or j == 0:
                state = state + 1
                stateArray[state] = newChar
                checkArray[state] = father_state
                character = newChar
                # 判断当前字符是否和上一字符是同一个父结点
                if father_state == checkArray[state-1]:
                    index = query_next_index(nextArray, father_state) + \
                                        ord(newChar) + baseArray[father_state]
                    nextArray[int(index)] = state
                # 否则不是同一父结点，则父节点的状态值加一
                else:
                    # 分配当前字符的 nextValue
                    nextIndex = distribute_next_value(nextArray)
                    nextArray[int(nextIndex)] = state
                    # 计算前一字符的 base 值
                    baseArray[father_state] = nextIndex - query_next_index(nextArray, father_state) - ord(newChar)
            fatherArray[j] = state
    checkArray[0] = 0

    return nextArray, baseArray, checkArray, stateArray, outputArray


def cal_next_space(nextArray):
    """
    Next表中空间占用的百分比
    :param nextArray:next 表
    :return:空间占用百分比
    """
    return max(nextArray+1) / len(nextArray)


def transfer(state, inputChar, nextArray, baseArray, checkArray, failArray):
    """
    读入字符后，当前状态发生转移后的状态值
    :param state: 当前状态值
    :param inputChar: 输入字符
    :param nextArray: next 表
    :param baseArray: base 表
    :param checkArray: check 表
    :param failArray: fail 函数
    :return: 转移状态值
    """
    try:
        index = query_next_index(nextArray, state) + ord(inputChar) + baseArray[state]
        nextState = nextArray[index]
        if checkArray[nextState] == state:  # 未失效失效
            return nextState
        failState = failArray[state]
        index = query_next_index(nextArray, failState) + ord(inputChar) + baseArray[failState]
        failNextState = nextArray[index]
        if checkArray[failNextState] == failState:  # 只需比较一次失效状态的结果即可
            return failNextState
        else:
            return 0
    except IndexError:
        failState = failArray[state]
        index = query_next_index(nextArray, failState) + ord(inputChar) + baseArray[failState]
        if index < 0:
            return 0
        failNextState = nextArray[index]
        if checkArray[failNextState] == 0:  # 只需比较一次失效状态的结果即可
            return failNextState
        else:
            return 0


def create_fail_table(nextArray, baseArray, checkArray, stateArray, outputArray):
    """
    创建失效函数，并更新输出集
    :param nextArray: next 表
    :param baseArray: base 表
    :param checkArray: check 表
    :param stateArray: 状态表
    :param outputArray: 输出表
    :return: 失效函数，输出集
    """
    failArray = np.zeros(len(baseArray), dtype=int)  # 失效函数，初始化都为 0
    stateNum = max(nextArray)
    for state in range(1, stateNum + 1):
        childrenList = query_children(checkArray, state)
        for child in childrenList:
            # 父结点的 fail 状态输入当前字符，转移后的状态值即为子结点的fail值
            fatherFail = failArray[state]   # 父结点的失效结点
            index = query_next_index(nextArray, fatherFail) + ord(stateArray[child]) + baseArray[fatherFail]
            failState = nextArray[index]
            if checkArray[failState] == fatherFail:
                failArray[child] = failState
                # 把失效状态的输出并入当前状态的输出表中
                if failState in outputArray.keys():
                    outputArray[child] += outputArray[failState]
            else:
                failArray[child] = nextArray[0]

    return failArray, outputArray


def match_text(detectText, nextArray, baseArray, checkArray, failArray, outputArray):
    """
    利用预生成的 next, base, check 表和失效函数以及输出集来匹配待检测文本
    :param detectText: 待检测文本
    :param nextArray: next 表
    :param baseArray: base 表
    :param checkArray: check 表
    :param failArray: 失效函数
    :param outputArray: 输出集
    :return: null
    """
    textLen = len(detectText)
    state = 0
    print("state:")
    for i in range(textLen):
        newState = transfer(state, detectText[i].lower(), nextArray, baseArray, checkArray, failArray)
        print("Input character ", i+1, ":", state, "--", detectText[i], "-->", newState)
        state = newState
        if state in outputArray.keys():
            print("Output:", end="")
            for output in outputArray[state]:
                print(output, " ", end="")
            print("\n", end="")


if __name__ == '__main__':
    file_path = "pattern.txt"
    pattern_array = read_patterns(file_path)
    print("The pattern array is ", pattern_array)
    text_path = "detectText.txt"
    detect_text = read_text(text_path)
    print("The text array is ", detect_text)
    pre_process(pattern_array)
    next_array, base_array, check_array, state_array, output_array = pre_process(pattern_array)
    print("The next table is ", next_array)
    print("The base table is ", base_array)
    print("The check table is ", check_array)
    print("The state table is ", state_array)
    fail_table, output_array = create_fail_table(next_array, base_array, check_array, state_array, output_array)
    print("The fail table is ", fail_table)
    print("The output table is ", output_array)
    match_text(detect_text, next_array, base_array, check_array, fail_table, output_array)
    print("The next space occupancy ratio is ", cal_next_space(next_array))

