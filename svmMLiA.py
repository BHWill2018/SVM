import numpy as np

#opens up the file and parses each line into class labels and data matrix
def loadDataSet(fileName):
	dataMat = []; labelMat = []
	fr = open(fileName)
	for line in fr.readlines():
		lineArr = line.strip().split('\t')
		dataMat.append([float(lineArr[0]),float(lineArr[1])])
		labelMat.append(float(lineArr[2]))
	return dataMat,labelMat

#i is the index of first alpha, m is the total number of alphas
def selectJrand(i,m):
	print("i= %d" %i)
	j = i;
	print("i = %d, j= %d" %(i,j))
	while(j == i):#A value is randomly chosen and returned as long as it's not equal to the input i
		j = int(np.random.uniform(0,m))
		print("iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiijjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjjj")
		print("i = %d, j= %d" %(i,j))
	return j

#clips alpha values if > H or < L
def clipAlpha(aj,H,L):
	if aj > H:
		aj = H
	if L > aj:
		aj = L
	return aj

#the simplified SMO algorithm
#C:contant,toler:tolerance,maxIter:maximum number of iterations
def smoSimple(dataMatIn,classLabels,C,toler,maxIter):
	dataMatrix = np.mat(dataMatIn); labelMat = np.mat(classLabels).transpose()
	b = 0
	m,n = np.shape(dataMatrix)
	print("m = %d, n = %d " % (m,n))
	alphas = np.mat(np.zeros((m,1)))
	iter = 0
	while(iter < maxIter):
		alphaPairsChanged = 0
		#遍历整个集合
		for i in range(m):
			#fXi - 预测的类别
			fXi = float(np.multiply(alphas,labelMat).T * (dataMatrix * dataMatrix[i,:].T)) + b
			#Ei - 误差
			Ei = fXi - float(labelMat[i])
			print("i in range(m) = %d, m = %d" % (i,m))
			#if alphas can be changed, enter optimization
			#正间隔和负间隔都被测试，同时价差alpha不能等于0或C
			#Alphas will be clipped at 0 or C, so if they’re equal to these, they’re “bound” and can’t be increased or decreased, so
			#it’s not worth trying to optimize these alphas.
			if((labelMat[i] * Ei < -toler) and (alphas[i] < C )) or ((labelMat[i] * Ei > toler) and (alphas[i] > 0)):
				j = selectJrand(i,m) #randomly select second alpha
				fXj = float(np.multiply(alphas,labelMat).T * (dataMatrix * dataMatrix[j,:].T)) + b
				Ej = fXj - float(labelMat[j])
				alphaIold = alphas[i].copy() #旧值存储，later compare the new alphas with the old ones
				alphaJold = alphas[j].copy() #旧值存储，later compare the new alphas with the old ones
				#clamp alpha[j] between 0 and C
				if(labelMat[i] != labelMat[j]):
					L = max(0, alphas[j] - alphas[i])
					H = min(C, C + alphas[j] - alphas[i])
				else:
					L = max(0, alphas[j] + alphas[i] - C )
					H = min(C, alphas[j] + alphas[i])
				if L == H:
					print("L == H")
					continue
				#eta is the optimal amount to change alpha[j]
				eta = 2.0 * dataMatrix[i,:] * dataMatrix[j,:].T - \
						dataMatrix[i,:] * dataMatrix[i,:].T - \
						dataMatrix[j,:] * dataMatrix[j,:].T
				if eta >= 0:
					print("eta >= 0")
					continue
				#get a new alpha[j]
				alphas[j] -= labelMat[j] * (Ei - Ej) / eta
				#clip it
				alphas[j] = clipAlpha(alphas[j],H,L)
				#check if alpha[j] has changed a small amount, if so, quit the for loop
				if(abs(alphas[j] - alphaJold) < 0.00001):
					print("J not moving enough")
					continue
				#alpha[i] is changed by the same amount as alpha[j] but in opposite direction
				alphas[i] += labelMat[j] * labelMat[i] * (alphaJold - alphas[j])
				#优化完alpha[i]and alpha[j]后，设置一个常数项b
				b1 = b - Ei - labelMat[i] * (alphas[i] - alphaIold) * \
						dataMatrix[i,:] * dataMatrix[i,:].T - \
						labelMat[j] * (alphas[j] - alphaJold) * \
						dataMatrix[i,:] * dataMatrix[j,:].T
				b2 = b - Ej - labelMat[i] * (alphas[i] - alphaIold) * \
						dataMatrix[i,:] * dataMatrix[j,:].T - \
						labelMat[j] * (alphas[j] - alphaJold) * \
						dataMatrix[j,:] * dataMatrix[j,:].T
				#set the constant term
				if(0 < alphas[i]) and (C > alphas[i]):
					b = b1
				elif(0 < alphas[j]) and (C > alphas[j]):
					b = b2
				else:
					b = (b1 + b2) / 2.0
				alphaPairsChanged += 1
				print("iter: %d  i: %d, pairs changed %d" % (iter,i,alphaPairsChanged))
		#check if alpha updated, if so, iter = 0
		if(alphaPairsChanged == 0):
			iter += 1
		else:
			iter = 0
		print("iteration number: %d" % iter)
	return b,alphas

#use data structure to hold all of the important values
#kTup:包含核函数信息的元组
class optStruct:
	def __init__(self,dataMatIn,classLabels,C,toler,kTup):
#	def __init__(self,dataMatIn,classLabels,C,toler):
		self.X = dataMatIn
		self.labelMat = classLabels
		self.C = C
		self.tol = toler
		self.m = np.shape(dataMatIn)[0]
		self.alphas = np.mat(np.zeros((self.m,1)))
		self.b = 0
		self.eCache = np.mat(np.zeros((self.m,2)))  #eCache的第一列:eCache是否有效的标志位，
													#第二列:实际的E值。
		self.K = np.mat(np.zeros((self.m,self.m)))
		for i in range(self.m):
			self.K[:,i] = kernelTrans(self.X,self.X[i,:],kTup)

#calculate E
def calcEk(oS, k):
#	fXk = float(np.multiply(oS.alphas,oS.labelMat).T * (oS.X * oS.X[k,:].T)) + oS.b
	fXk = float(np.multiply(oS.alphas,oS.labelMat).T * oS.K[:,k] + oS.b)
	Ek = fXk - float(oS.labelMat[k])
	return Ek

#select the second alpha
def selectJ(i, oS, Ei):
	maxK = -1
	maxDeltaE = 0
	Ej = 0
	oS.eCache[i] = [1,Ei]
	validEcacheList = np.nonzero(oS.eCache[:,0].A)[0] #non zero list
	if(len(validEcacheList)) > 1:
		for k in validEcacheList:
			if k == i:
				continue
			Ek = calcEk(oS,k)
			deltaE = abs(Ei - Ek)
			if (deltaE > maxDeltaE):
				maxK = k
				maxDeltaE = deltaE
				Ej = Ek
		return maxK,Ej
	else:
		j = selectJrand(i,oS.m)
		Ej = calcEk(oS,j)
	return j,Ej

#calculate the error and puts it in the cache
def updateEk(oS, k):
	Ek = calcEk(oS,k)
	oS.eCache[k] = [1,Ek]

#Full Platt SMO optimization routine
def innerL(i,oS):
	Ei = calcEk(oS,i)
	if((oS.labelMat[i] * Ei < -oS.tol) and (oS.alphas[i] < oS.C )) or ((oS.labelMat[i] * Ei > oS.tol) and (oS.alphas[i] > 0)):
		j,Ej = selectJ(i,oS,Ei)
		alphaIold = oS.alphas[i].copy()
		alphaJold = oS.alphas[j].copy()
		if(oS.labelMat[i] != oS.labelMat[j]):
			L = max(0, oS.alphas[j] - oS.alphas[i])
			H = min(oS.C ,oS.C + oS.alphas[j] - oS.alphas[i])
		else:
			L = max(0, oS.alphas[j] + oS.alphas[i] - oS.C)
			H = min(oS.C,oS.alphas[j] + oS.alphas[i])
		if L == H:
			print("L == H")
			return 0
#		eta = 2.0 * oS.X[i,:] * oS.X[j,:].T - oS.X[i,:] * oS.X[i,:].T - oS.X[j,:] * oS.X[j,:].T
		#for kernel
		eta = 2.0 * oS.K[i,j] - oS.K[i,i] - oS.K[j,j]
		if eta >= 0:
			print("eta >= 0")
			return 0
		oS.alphas[j] -= oS.labelMat[j] * (Ei - Ej) / eta
		oS.alphas[j] = clipAlpha(oS.alphas[j],H,L)
		#update Error cache
		updateEk(oS,j)
		if(abs(oS.alphas[j] - alphaJold) < 0.00001):
			print("j not moving enough")
			return 0
		oS.alphas[i] += oS.labelMat[j] * oS.labelMat[i] * (alphaJold - oS.alphas[j])
		#update Error cache
		updateEk(oS,i)
#		b1 = oS.b - Ei - oS.labelMat[i] * (oS.alphas[i] - alphaIold) * oS.X[i,:] * oS.X[i,:].T - oS.labelMat[j] * (oS.alphas[j] - alphaJold) * oS.X[i,:] * oS.X[j,:].T
#		b2 = oS.b - Ej - oS.labelMat[i] * (oS.alphas[i] - alphaIold) * oS.X[i,:] * oS.X[j,:].T - oS.labelMat[j] * (oS.alphas[j] - alphaJold) * oS.X[j,:] * oS.X[j,:].T
		#for kernel
		b1 = oS.b - Ei - oS.labelMat[i] * (oS.alphas[i] - alphaIold) * oS.K[i,i] - oS.labelMat[j] * (oS.alphas[j] - alphaJold) * oS.K[i,j]
		b2 = oS.b - Ej - oS.labelMat[i] * (oS.alphas[i] - alphaIold) * oS.K[i,j] - oS.labelMat[j] * (oS.alphas[j] - alphaJold) * oS.K[j,j]
		if(0 < oS.alphas[i]) and (oS.C > oS.alphas[i]):
			oS.b = b1
		elif(0 < oS.alphas[j]) and (oS.C > oS.alphas[j]):
			oS.b = b2
		else:
			oS.b = (b1 + b2) / 2.0
		return 1
	else:
		return 0

def smoP(dataMatIn,classLabels,C,toler,maxIter,kTup = ('lin',0)):
	oS = optStruct(np.mat(dataMatIn),np.mat(classLabels).transpose(),C,toler,kTup)
	iter = 0
	entireSet = True
	alphaPairsChanged = 0
	while(iter < maxIter) and ((alphaPairsChanged > 0) or (entireSet)):
		alphaPairsChanged = 0
		#go over all values
		if entireSet:
			for i in range(oS.m):
				alphaPairsChanged += innerL(i,oS)
			print("fullSet, iter: %d i: %d, pairs changed %d" %(iter,i,alphaPairsChanged))
			iter += 1
		#go over non-bound values
		else:
			nonBoundIs = np.nonzero((oS.alphas.A > 0) * (oS.alphas.A < C))[0]
			for i in nonBoundIs:
				alphaPairsChanged += innerL(i,oS)
				print("non-bound,iter: %d, i: %d, pairs changed %d" % (iter,i,alphaPairsChanged))
			iter += 1
		if entireSet:
			entireSet = False
		elif(alphaPairsChanged == 0):
			entireSet = True
		print("iteration number: %d" % iter)
	return oS.b, oS.alphas

#w
def calcWs(alphas,dataArr,classLabels):
	X = np.mat(dataArr)
	labelMat = np.mat(classLabels).transpose()
	m,n = np.shape(X)
	w = np.zeros((n,1))
	for i in range(m):
		w += np.multiply(alphas[i] * labelMat[i],X[i,:].T)
	return w

def kernelTrans(X,A,kTup):
	m,n = np.shape(X)
	K = np.mat(np.zeros((m,1)))
	if kTup[0] == 'lin':
		K = X * A.T
	elif kTup[0] == 'rbf':
		for j in range(m):
			deltaRow = X[j,:] - A
			K[j] = deltaRow * deltaRow.T
		K = np.exp(K / (-1 * kTup[1] ** 2))
	else:
		raise NameError('Houston We have a problem -- That Kernel is not recognized!')
	return K

def testRbf(k1=1.3):
	dataArr, labelArr = loadDataSet('E:/python/machinelearning/机器学习实战课文相关下载/machinelearninginaction/Ch06/testSetRBF.txt')
	b,alphas = smoP(dataArr, labelArr, 200, 0.0001, 10000, ('rbf', k1)) #C=200 important
	datMat = np.mat(dataArr)
	labelMat = np.mat(labelArr).transpose()
	svInd = np.nonzero(alphas.A > 0)[0]
	sVs = datMat[svInd] #get matrix of only support vectors
	labelSV = labelMat[svInd];
	print("there are %d Support Vectors" % np.shape(sVs)[0])

	m,n = np.shape(datMat)
	errorCount = 0
	for i in range(m):
		kernelEval = kernelTrans(sVs,datMat[i,:],('rbf', k1))
		predict = kernelEval.T * np.multiply(labelSV, alphas[svInd]) + b
		if np.sign(predict) != np.sign(labelArr[i]): 
			errorCount += 1
	print("the training error rate is: %f" % (float(errorCount) / m))

	dataArr,labelArr = loadDataSet('E:/python/machinelearning/机器学习实战课文相关下载/machinelearninginaction/Ch06/testSetRBF2.txt')
	errorCount = 0
	datMat = np.mat(dataArr)
	labelMat = np.mat(labelArr).transpose()
	m,n = np.shape(datMat)
	for i in range(m):
		kernelEval = kernelTrans(sVs,datMat[i,:],('rbf', k1))
		predict=kernelEval.T * np.multiply(labelSV, alphas[svInd]) + b
		if np.sign(predict) != np.sign(labelArr[i]): 
			errorCount += 1    
	print("the test error rate is: %f" % (float(errorCount) / m))    


def img2vector(filename):
	returnVect = np.zeros((1,1024))
	fr = open(filename)

	for i in range(32):
		lineStr = fr.readline()
		for j in range(32):
			returnVect[0,32*i+j] = int(lineStr[j])
			#print("i=%d, j=%d" %(i,j))
	return returnVect


def loadImages(dirName):
	from os import listdir
	hwLabels = []
	trainingFileList = listdir(dirName)
	m = len(trainingFileList)
	trainingMat = np.zeros((m,1024))
	for i in range(m):
		fileNameStr = trainingFileList[i]
		fileStr = fileNameStr.split('.')[0]
		classNumStr = int(fileStr.split('_')[0])
		if classNumStr == 9:
			hwLabels.append(-1)
		else:
			hwLabels.append(1)
		trainingMat[i,:] = img2vector('%s/%s' % (dirName,fileNameStr))
	return trainingMat, hwLabels

def testDigits(kTup = ('rbf',10)):
	dataArr, labelArr = loadImages('E:/python/machinelearning/机器学习实战课文相关下载/machinelearninginaction/Ch06/digits/trainingDigits')
	b,alphas = smoP(dataArr,labelArr,200,0.0001,10000,kTup)
	datMat = np.mat(dataArr);
	labelMat = np.mat(labelArr).transpose()
	svInd = np.nonzero(alphas.A > 0)[0]
	sVs = datMat[svInd]
	labelSV = labelMat[svInd]
	print("there are %d Support Vectors" % np.shape(sVs)[0])
	m,n = np.shape(datMat)
	errorCount = 0
	for i in range(m):
		kernelEval = kernelTrans(sVs,datMat[i,:],kTup)
		predict = kernelEval.T * np.multiply(labelSV,alphas[svInd]) + b
		if np.sign(predict) != np.sign(labelArr[i]):
			errorCount += 1
	print("the training error rate is : %f" % (float(errorCount) / m))
	dataArr,labelArr = loadImages('E:/python/machinelearning/机器学习实战课文相关下载/machinelearninginaction/Ch06/digits/testDigits')
	errorCount = 0
	datMat = np.mat(dataArr)
	labelMat = np.mat(labelArr).transpose()
	m,n = np.shape(datMat)
	for i in range(m):
		kernelEval = kernelTrans(sVs,datMat[i,:],kTup)
		predict = kernelEval.T * np.multiply(labelSV,alphas[svInd]) + b
		if np.sign(predict) != np.sign(labelArr[i]):
			errorCount += 1
	print("the test error rate is : %f" %(float(errorCount) / m))

