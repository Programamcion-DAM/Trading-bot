class TAHIEL1(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)#La fecha inicial del backtest el 1 de enero de 202o
        self.SetEndDate(2021,12,31)#El backtest dura 1 años.
        self.SetCash(100000)  #Cash inicial de la cuenta en 100000 dolares
        self.crypto = self.AddCrypto("BTCUSD", Resolution.Minute).Symbol #Añadimos la crypto
        
        self.SetBrokerageModel(BrokerageName.Bitfinex,AccountType.Margin)
        
        self.SetWarmUp(timedelta(days = 201))#Periodo para que se inicie la ema antes de que comience el algoritmo
        self.ema = self.EMA(self.crypto,200,Resolution.Daily)#Creamos la ema 
        
        self.amount = 0 #En esta variable almacenaré la cantidad de cryptos que haya comprado por operación
        self.entryPrice = 0 #Almacenaremos el precio con el que entramos en la operacion
        
        #Creamos las variables de los takeprofit y stoploss
        self.SL = None
        self.TP1 = None
        self.TP2 = None
    
    #Este metodo se ejecuta cada segundo debido a la resolucion en que he pedido que me pasen los datos
    def OnData(self, data):
        #Adquirimos el precio de la crypto
        cryptoPrice = data[self.crypto].Close
        
        #Comprobamos si esta por encima de la ema
        if(cryptoPrice > self.ema.Current.Value):
            if not(self.Portfolio.Invested):
                self.amount = round((self.Portfolio.Cash*0.3)/cryptoPrice,2) #Calculamos cuantas compramos con el 30% cuenta
                self.entryPrice = cryptoPrice #Guardamos el precio de entrada
                
                #Compramos la cantidad de crytos que acabamos de calcular 
                self.MarketOrder(self.crypto,self.amount)
                
                #Configuramos el stop loss 1% abajo del precio de entrada 
                self.SL = self.StopMarketOrder(self.crypto,-self.amount,self.entryPrice *0.99)
                
                #Configuramos el primer take profit 0.1% arriba, donde sacamos la mitad de la posicion
                self.TP1 = self.LimitOrder(self.crypto,-self.amount/2,self.entryPrice * 1.01)
                
                #Configuramos el segundo take profit 0.5% arriba, donde sacamos la otra mitad de la posicion
                self.TP2 = self.LimitOrder(self.crypto,-self.amount/2,self.entryPrice * 1.03)
        
        
    #Metodo donde actualizaremos las ordenes
    def OnOrderEvent(self, orderEvent):
        if(orderEvent.Status != OrderStatus.Filled):
            return
        if(self.SL == None or self.TP1 == None or self.TP2 == None):
            return
        
        order = self.Transactions.GetOrderById(orderEvent.OrderId)
        
        #Si ha saltado el stop loss cancelamos los dos takeProfit(comprobando si el primero no ha sido ejecutado)
        if(self.SL.OrderId == order.Id):
            if(self.TP1.Status == OrderStatus.Submitted):
                self.TP1.Cancel()
            
            self.TP2.Cancel()
        
        #Si ha saltado el take profit 1 movemos el stop loss a ese precio y ponemos que ya solo venda la mitad de lo que queda
        if(self.TP1.OrderId == order.Id):
            self.SL.UpdateQuantity(-self.amount/2)
            self.SL.UpdateStopPrice(self.entryPrice)
        
        #Si ha saltado el take profit 2 cancelamos el stoploss
        if(self.TP2.OrderId == order.Id):
            self.SL.Cancel()
