stats <- read.csv("./contracts.csv", stringsAsFactors = F)

# Removing buggy entries
stats <- stats[!is.na(suppressWarnings(as.numeric(stats$Trans))),]
# Converting transitions to numbers
stats$Trans <- as.numeric(stats$Trans)
maxTrans <- max(stats$Trans)
minTrans <- min(stats$Trans)

##################################
# Margins
##################################
topMargin <- 0.3
leftMargin <- 0.3
bottomMargin <- 3.9
rightMargin <- 0.3
myMgp = c(2.7, 1, 0)

cexSize <- 2.0
cexLabFont <- 2.0
cexAxis <- 1.4

wid <- 10
hei <- 5

###############################################
# Maximal size of GE signature
###############################################
pdf(file = "../fig/maxgesize.pdf",  
    width = wid, 
    height = hei)

par(mfrow=c(1, 1), 
    mar=c(bottomMargin, leftMargin, topMargin, rightMargin),
    oma=c(0, 2, 0, 0), mgp=myMgp)

col1 = c("blue")
shp1  = 19
leg1  = c("Size of the largest good enough signature")
plot(stats$MaxGESize ~ stats$Trans,
     xlab="Number of transitions in a contract",
     ylab = "",
     col = col1, 
     pch=shp1,
     cex=cexSize, 
     cex.lab=cexLabFont,
     cex.axis=cexAxis,
     las = 1,
     xaxt="n",
     )
axis(1, xaxp=c(minTrans, maxTrans, maxTrans - minTrans), las=1, cex.axis=cexAxis)
legend("topleft", 
       leg1, 
       cex=cexSize, 
       col=col1,
       pch=shp1)

dev.off()

# Correlation
corLargest <- cor(stats$MaxGESize, stats$Trans)

###############################################
# Number of maximal GE signatures
###############################################
pdf(file = "../fig/maxgenumber.pdf", 
    width = wid,
    height = hei)

par(mfrow=c(1, 1), 
    mar=c(bottomMargin, leftMargin, topMargin, rightMargin),
    oma=c(0, 2, 0, 0), mgp=myMgp)

col2 = c("red")
shp2  = 17
leg2  = c("Number of maximal good enough signatures")
maxMaxGENum <- max(stats$MaxGENum)

plot(stats$MaxGENum ~ stats$Trans,
     xlab="Number of transitions in a contract",
     col = col2, 
     pch=shp2,
     cex=cexSize, 
     cex.lab=cexLabFont,
     cex.axis=cexAxis,
     las = 1,
     xaxt="n",
)
axis(1, xaxp=c(minTrans, maxTrans, maxTrans - minTrans), las=1,cex.axis=cexAxis)
# axis(2, yaxp=c(0, maxMaxGENum, maxMaxGENum), las=1)
legend("topleft", 
       leg2, 
       cex=cexSize, 
       col=col2,
       pch=shp2)

dev.off()

corNumber <- cor(stats$MaxGENum, stats$Trans)

###########################################
# Distribution of sharding ratios
###########################################
pdf(file = "../fig/ratios.pdf", 
    width = wid,
    height = hei)

par(mfrow=c(1, 1), 
    mar=c(bottomMargin, leftMargin, topMargin, rightMargin),
    oma=c(0, 2, 0, 0), mgp=myMgp)

hist(stats$ShardingRatio,
     col = "lightblue",
     xlim=c(-0,1), 
     breaks = 20,
     main = "",
     xlab="Sharding ratios",
     ylab="Frequency",
     cex=cexSize, 
     cex.lab=cexLabFont,
     cex.axis=cexAxis,)

dev.off()

##############################
# Distribution of transitions
##############################
pdf(file = "../fig/trans.pdf", 
    width = wid,
    height = 3)

par(mfrow=c(1, 1), 
    mar=c(bottomMargin-1.5, leftMargin, topMargin + 1.0, rightMargin),
    oma=c(0, 2, 0, 0), mgp=myMgp)

barplot(table(stats$Trans),
     col = "coral",
     main = "",
     xlab="",
     cex=1.7, 
     las = 1,
     cex.axis=2.7)

dev.off()

###########################


###########################
# Quantiles
###########################

# summary(stats$ShardingRatio)
# 
# barplot(table(stats$Trans))
# 
# cor(stats$ShardingRatio, stats$Trans)
