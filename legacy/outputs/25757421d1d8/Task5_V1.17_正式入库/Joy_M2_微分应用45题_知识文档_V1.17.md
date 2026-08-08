# Joy M2 微分应用45题知识文档（V1.17）

> 数据源：V1.17 SQLite `complete_questions_v2`；一道完整题一条记录，不拆分小问。

## 数据摘要

- 完整题：45题；正式发布：45题。
- 难度：L2×8、L3×17、L4×16、L5×4。
- 主类型：切线与法线×6、变率×5、最值与最优化×5、极值与曲线性质×24、综合微分应用×5。
- 答案状态：45题均为 `source_provided`，并已完成逐题数学复核。

## 教材例题（8题）

### 1. `M2QD-DA-EXAMPLE-Q1`

- 原题号：EXAMPLE-Q1；分值：7；难度：Level 3。
- 主类型：切线与法线；标签：过指定点的切线、切点未知。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=26-\frac{108}{x}$ ,where $0<x<20$ .
(a) Find $\frac{d y}{d x}$ .
(b) If a tangent $L$ to $C$ passes through the point（ 10,20 ）,find the equation of $L$ .

#### 中文审定题干

考虑曲线 $C:y=26-\frac{108}{x}$，其中 $0<x<20$。
(a) 求 $\frac{dy}{dx}$。
(b) 若曲线 $C$ 的一条切线 $L$ 通过点 $(10,20)$，求 $L$ 的方程。（共 7 分）

#### 核验答案

(a) $y=26-108x^{-1}$，故 $\frac{dy}{dx}=108x^{-2}=\frac{108}{x^2}$。
(b) 设切点为 $\left(h,26-\frac{108}{h}\right)$。切线斜率同时为 $\frac{108}{h^2}$ 及 $\frac{(26-108/h)-20}{h-10}$，所以
$$\frac{108}{h^2}=\frac{6-108/h}{h-10}\Longrightarrow h^2-36h+180=0.$$
因此 $h=6$ 或 $30$；由 $0<h<20$，舍去 $h=30$。当 $h=6$ 时斜率为 $3$，而切线通过 $(10,20)$，故
$$y-20=3(x-10),\qquad L:3x-y-10=0.$$

#### 校订记录

- solution_original：原式既没有减去外点的纵坐标 20，又把横坐标差误成 $h-1$；与下一行及后续推导不一致。当前抽取答案已采用正确式，审计在此补齐校订轨迹。

### 2. `M2QD-DA-EXAMPLE-Q2`

- 原题号：EXAMPLE-Q2；分值：未标示；难度：Level 3。
- 主类型：极值与曲线性质；标签：极大点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Find the maximum point（s）of the graph of $y=\frac{x^{2}+3 x+3}{x+2}$ .

#### 中文审定题干

求曲线 $y=\frac{x^2+3x+3}{x+2}$（$x\ne-2$）的极大点。

#### 核验答案

设 $f(x)=\frac{x^2+3x+3}{x+2}$，则
$$f'(x)=\frac{x^2+4x+3}{(x+2)^2}=\frac{(x+1)(x+3)}{(x+2)^2}.$$
驻点的横坐标为 $x=-3,-1$。当 $x$ 递增经过 $-3$ 时，$f'(x)$ 由正变负，故 $x=-3$ 对应极大点；$f(-3)=-3$。所以极大点为 $(-3,-3)$。

### 3. `M2QD-DA-EXAMPLE-Q3`

- 原题号：EXAMPLE-Q3；分值：4；难度：Level 4。
- 主类型：最值与最优化；标签：全局最小值。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=5 x^{8}+56 x^{5}-160 x^{2}$ .Find the least value of $f(x)$ .

#### 中文审定题干

定义 $f(x)=5x^8+56x^5-160x^2$。求 $f(x)$ 的最小值。（4 分）

#### 核验答案

$$f'(x)=40x^7+280x^4-320x=40x(x^3-1)(x^3+8).$$
故驻点横坐标为 $x=-2,0,1$。由 $f'$ 的符号依次为负、正、负、正，可知 $x=-2$ 与 $x=1$ 为极小位置，$x=0$ 为极大位置。
$$f(-2)=-1152,\qquad f(0)=0,\qquad f(1)=-99.$$
又因 $x\to\pm\infty$ 时 $f(x)\to+\infty$，所以全局最小值为 $-1152$。

### 4. `M2QD-DA-EXAMPLE-Q4`

- 原题号：EXAMPLE-Q4；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：拐点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $y=\left(x-x^{2}\right) e^{-x}$ .
(a) Find $\frac{d y}{d x}$ and $\frac{d^{2} y}{d x^{2}}$ .
(b) Someone claims that there is only one point of inflexion of the graph of $y=\left(x-x^{2}\right) e^{-x}$ .Do you agree？Explain your answer.

#### 中文审定题干

设 $y=(x-x^2)e^{-x}$。
(a) 求 $\frac{dy}{dx}$ 及 $\frac{d^2y}{dx^2}$。
(b) 某人声称 $y=(x-x^2)e^{-x}$ 的图像只有一个拐点。你是否同意？解释你的答案。（共 6 分）

#### 核验答案

(a)
$$\frac{dy}{dx}=(x^2-3x+1)e^{-x},\qquad \frac{d^2y}{dx^2}=(-x^2+5x-4)e^{-x}.$$
(b) 因 $e^{-x}>0$，$\frac{d^2y}{dx^2}=0$ 等价于 $-x^2+5x-4=0$，故 $x=1,4$。二阶导数在 $(-\infty,1),(1,4),(4,\infty)$ 上的符号依次为负、正、负，两处均变号。因此图像有两个拐点：
$$(1,0)\quad\text{及}\quad(4,-12e^{-4}).$$
所以不同意该声称。

#### 校订记录

- solution_original：题目明确要求两个导数，原题解答案边界漏印二阶导数；当前抽取答案已补入并经独立求导验证。

### 5. `M2QD-DA-EXAMPLE-Q5`

- 原题号：EXAMPLE-Q5；分值：3；难度：Level 2。
- 主类型：极值与曲线性质；标签：渐近线。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=\frac{x^{2}+5 x+1}{x+2}$ for all $x \neq-2$ .Denote the graph of $y=f(x)$ by $C$ .Find the asymptote（s）of $C$ .

#### 中文审定题干

对所有 $x\ne-2$，定义 $f(x)=\frac{x^2+5x+1}{x+2}$，并把 $y=f(x)$ 的图像记为 $C$。求 $C$ 的所有渐近线。（3 分）

#### 核验答案

当 $x=-2$ 时分母为零而分子为 $-5\ne0$，故 $x=-2$ 是垂直渐近线。又
$$f(x)=\frac{x^2+5x+1}{x+2}=x+3-\frac{5}{x+2}.$$
当 $x\to\pm\infty$ 时，$-\frac{5}{x+2}\to0$，故 $y=x+3$ 是斜渐近线。答案为 $x=-2$ 及 $y=x+3$。

### 6. `M2QD-DA-EXAMPLE-Q6`

- 原题号：EXAMPLE-Q6；分值：12；难度：Level 5。
- 主类型：综合微分应用；标签：切点未知求法线、几何最优化、相关变化率、面积变化、建立变量关系、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=\ln x$ ,where $x>1$ .Let $P$ be a moving point lying on $C . L$ is a line that passes through $P$ and is perpendicular to the tangent to $C$ at $P . L$ cuts the $x$－axis at the point $Q$ while the vertical line passing through $P$ cuts the $x$－axis at the point $R$ .
(a) Denote the $x$－coordinate of $P$ by $p$ .Find the $x$－coordinate of $Q$ in terms of $p$ .
(b) Find the greatest area of $\triangle P Q R$ .
(c) Let $O$ be the origin.It is given that $O P$ increases at a rate not exceeding $2 e^{2}$ units per second.Someone claims that the area of $\triangle P Q R$ increases at a rate lower than 1 square unit per second when the $x$－coordinate of $P$ is $e$ .Is the claim correct？Explain your answer.

#### 中文审定题干

考虑曲线 $C:y=\ln x$，其中 $x>1$。设 $P$ 为 $C$ 上的一个动点。直线 $L$ 通过 $P$，并垂直于 $C$ 在 $P$ 处的切线。$L$ 与 $x$ 轴交于点 $Q$，过 $P$ 的竖直线与 $x$ 轴交于点 $R$。
(a) 设 $P$ 的 $x$ 坐标为 $p$，以 $p$ 表示 $Q$ 的 $x$ 坐标。（3 分）
(b) 求 $\triangle PQR$ 的最大面积。（5 分）
(c) 设 $O$ 为原点。已知 $OP$ 以不超过每秒 $2e^2$ 个单位的速率增加。某人声称：当 $P$ 的 $x$ 坐标为 $e$ 时，$\triangle PQR$ 的面积以低于每秒 1 个平方单位的速率增加。该声称是否正确？解释你的答案。（4 分）

#### 核验答案

(a) $P=(p,\ln p)$，切线斜率为 $1/p$，故法线 $L$ 的斜率为 $-p$。设 $Q=(a,0)$，则
$$\frac{-\ln p}{a-p}=-p\Longrightarrow a=\frac{p^2+\ln p}{p}.$$
(b) 设三角形面积为 $A$，则
$$A=\frac12(a-p)\ln p=\frac{(\ln p)^2}{2p},\qquad \frac{dA}{dp}=\frac{\ln p(2-\ln p)}{2p^2}.$$
因 $p>1$，导数在 $1<p<e^2$ 为正、在 $p>e^2$ 为负，所以最大面积在 $p=e^2$ 取得，等于 $\frac{2}{e^2}$ 平方单位。
(c) 令 $s=OP=\sqrt{p^2+(\ln p)^2}$。在 $p=e$ 时，
$$\frac{dA}{dp}=\frac1{2e^2},\qquad \frac{ds}{dp}=\frac{\sqrt{e^2+1}}{e}.$$
由 $0\le ds/dt\le2e^2$，得
$$0\le\frac{dp}{dt}\le\frac{2e^3}{\sqrt{e^2+1}},\qquad 0\le\frac{dA}{dt}\le\frac{e}{\sqrt{e^2+1}}<1.$$
因此该声称正确。

#### 校订记录

- question_text_original：冻结 MMD 把曲线符号 $C$、句点及下一句的直线符号 $L$ 并入同一数学环境，造成英文与公式定界错误；中文行清楚表明应分为两句。缺少原扫描页，故不进一步归因于 Mathpix。
- solution_original：原 MMD 的最终结论 $dA/dt<1$ 本身正确；审计答案补足中间推导，并给出可由题设推出的更紧精确上界 $dA/dt\le e/\sqrt{e^2+1}<1$。缺少原扫描页，不把 MMD 的简略写法判为数学错误或归因于 Mathpix。

### 7. `M2QD-DA-EXAMPLE-Q7`

- 原题号：EXAMPLE-Q7；分值：6；难度：Level 4。
- 主类型：变率；标签：相关变化率、几何量变化、面积变化、链式法则建模、建立变量关系。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C_{1}: y=2^{x-1}$ ,where $x>0$ .Denote the origin by $O$ .Let $P(u, v)$ be a moving point on $C_{1}$ such that the area of the circle with $O P$ as a radius decreases at a constant rate of $8 \pi$ square units per second.The vertical line passing through $P$ cuts the $x$－axis at the point $Q$ . Find the rate of change of the area of $\triangle O P Q$ when $u=2$ .

#### 中文审定题干

考虑曲线 $C_1:y=2^{x-1}$，其中 $x>0$。设 $O$ 为原点，$P(u,v)$ 为 $C_1$ 上的一个动点。以 $OP$ 为半径的圆，其面积以每秒 $8\pi$ 个平方单位的恒定速率减少。过 $P$ 的竖直线与 $x$ 轴交于点 $Q$。求当 $u=2$ 时 $\triangle OPQ$ 面积的变率。（6 分）

#### 核验答案

设以 $OP$ 为半径的圆的面积为 $A$。因 $v=2^{u-1}$，
$$A=\pi(u^2+v^2),\qquad \frac{dA}{dt}=2\pi\left(u\frac{du}{dt}+v\frac{dv}{dt}\right)=-8\pi,$$
且 $\frac{dv}{dt}=v\ln2\frac{du}{dt}$。所以
$$\frac{du}{dt}=\frac{-4}{u+2^{2u-2}\ln2},\qquad \left.\frac{du}{dt}\right|_{u=2}=\frac{-2}{1+2\ln2}.$$
设 $\triangle OPQ$ 面积为 $S$，则
$$S=\frac12uv=u2^{u-2},\qquad \frac{dS}{dt}=(1+u\ln2)2^{u-2}\frac{du}{dt}.$$
代入 $u=2$ 得
$$\left.\frac{dS}{dt}\right|_{u=2}=(1+2\ln2)\frac{-2}{1+2\ln2}=-2.$$
因此所求变率为每秒 $-2$ 个平方单位，即面积正以每秒 2 个平方单位减少。

#### 校订记录

- solution_original：来源 MMD 的圆面积求导式被 OCR 截断，漏去 $dv/dt$ 及闭合结构；当前抽取答案已重建正确关系并经独立复算验证。

### 8. `M2QD-DA-EXAMPLE-Q8`

- 原题号：EXAMPLE-Q8；分值：9；难度：Level 4。
- 主类型：综合微分应用；标签：极大点、极小点、二阶导数判别法、已知切点求切线、凹凸性、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=e^{x} \sin x$ for all $x \in[0,2 \pi]$ .Denote the graph of $y=f(x)$ by $G$ .
(a) Find $f^{\prime}(x)$ and $f^{\prime \prime}(x)$ .
(b) Find the maximum point（s）and the minimum point（s）of $G$ .
(c) Let $L$ be the tangent to $G$ at $x=\pi$ .
(i) Find the equation of $L$ .
(ii) By considering $f^{\prime \prime}(x)$ ,explain why $G$ lies below $L$ in the interval $\left(\frac{\pi}{2}, \frac{3 \pi}{2}\right)$ .

#### 中文审定题干

对所有 $x\in[0,2\pi]$，定义 $f(x)=e^x\sin x$，并把 $y=f(x)$ 的图像记为 $G$。
(a) 求 $f'(x)$ 及 $f''(x)$。（3 分）
(b) 求 $G$ 的极大点及极小点。（3 分）
(c) 设 $L$ 为 $G$ 在 $x=\pi$ 处的切线。
(i) 求 $L$ 的方程。
(ii) 通过考察 $f''(x)$，解释为什么在区间 $\left(\frac{\pi}{2},\frac{3\pi}{2}\right)$ 内，$G$ 不高于 $L$，并且除切点 $(\pi,0)$ 外严格位于 $L$ 的下方。（3 分）

#### 核验答案

(a)
$$f'(x)=e^x(\sin x+\cos x),\qquad f''(x)=2e^x\cos x.$$
(b) $f'(x)=0$ 给出 $x=\frac{3\pi}{4},\frac{7\pi}{4}$。因
$$f''\left(\frac{3\pi}{4}\right)<0,\qquad f''\left(\frac{7\pi}{4}\right)>0,$$
极大点和极小点分别为
$$\left(\frac{3\pi}{4},\frac{e^{3\pi/4}}{\sqrt2}\right),\qquad \left(\frac{7\pi}{4},-\frac{e^{7\pi/4}}{\sqrt2}\right).$$
(c)(i) $f(\pi)=0$ 且 $f'(\pi)=-e^\pi$，故
$$L:y=-e^\pi(x-\pi).$$
(ii) 在 $\left(\frac{\pi}{2},\frac{3\pi}{2}\right)$ 内，$e^x>0$ 且 $\cos x<0$，故 $f''(x)<0$，图像严格凹向下。凹函数的图像不高于其任一切线，因此 $f(x)\le -e^\pi(x-\pi)$；只在切点 $x=\pi$ 取等号，其余点严格小于。

#### 校订记录

- question_text_original：$L$ 是 $G$ 在区间内部 $x=\pi$ 处的切线，故两图像在 $(\pi,0)$ 必然相交；“整段严格在下方”不成立。
- question_text_zh：中文忠实翻译了英文的非严格表述问题，需把切点处等号明确写出。
- solution_original：来源结论漏掉切点处的等号；导数和切线计算本身正确。

## 应试训练（14题）

### 1. `M2QD-DA-TRAIN-Q1`

- 原题号：TRAIN-Q1；分值：6；难度：Level 3。
- 主类型：切线与法线；标签：切点未知、隐函数求导。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

It is given that the curve $x \ln y^{2}+y^{2}=9$ cuts the $y$－axis at two points.Find the equations of the tangents to the curve at these two points.

#### 中文审定题干

已知曲线 $x\ln y^{2}+y^{2}=9$ 与 $y$ 轴相交于两点。求曲线在这两个交点处的切线方程。

#### 核验答案

令 $x=0$，得 $y=\pm3$。对 $x\ln y^2+y^2=9$ 关于 $x$ 隐式求导：$\ln y^2+(2x/y+2y)\,dy/dx=0$，故 $dy/dx=-y\ln y^2/(2x+2y^2)$。在 $(0,3)$ 处斜率为 $-\ln3/3$，切线为 $y=-(\ln3)x/3+3$；在 $(0,-3)$ 处斜率为 $\ln3/3$，切线为 $y=(\ln3)x/3-3$。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 2. `M2QD-DA-TRAIN-Q2`

- 原题号：TRAIN-Q2；分值：6；难度：Level 4。
- 主类型：切线与法线；标签：过指定点的切线、切点未知、隐函数求导。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Find the equations of the two tangents to the curve $C: x^{2}+2 x y-y^{2}=1$ which pass through the point $A(0,-1)$ .

#### 中文审定题干

求曲线 $C:x^{2}+2xy-y^{2}=1$ 的两条经过点 $A(0,-1)$ 的切线方程。

#### 核验答案

隐式求导得 $dy/dx=(x+y)/(y-x)$。设切点为 $P(a,b)$，则 $P$ 在曲线上，且切线经过 $A$，所以 $(a+b)/(b-a)=(b+1)/a$。结合 $a^2+2ab-b^2=1$ 得 $b=a+1$，继而 $a=1$ 或 $a=-1$。相应切点为 $(1,2)$、$(-1,0)$，两条切线分别为 $3x-y-1=0$ 和 $x+y+1=0$。可能的竖直切线不经过 $A$，故没有遗漏。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 3. `M2QD-DA-TRAIN-Q3`

- 原题号：TRAIN-Q3；分值：4；难度：Level 2。
- 主类型：极值与曲线性质；标签：极小点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the continuous function $f(x)=\frac{x^{2}-1}{x^{2}+3}$ .Find all the extreme point（s）of the graph of $y=f(x)$ .

#### 中文审定题干

考虑连续函数 $f(x)=\dfrac{x^{2}-1}{x^{2}+3}$。求曲线 $y=f(x)$ 的所有极值点。

#### 核验答案

$f'(x)=8x/(x^2+3)^2$。由于分母恒正，$f'(x)<0$（$x<0$），$f'(0)=0$，$f'(x)>0$（$x>0$），故函数在 $x=0$ 处由减转增。又 $f(0)=-1/3$，所以唯一极值点为极小点 $(0,-1/3)$。

#### 校订记录

- marks_total：题面未印分值，但出版社答案的分项标记合计4分且末行明确标示（4）。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 4. `M2QD-DA-TRAIN-Q4`

- 原题号：TRAIN-Q4；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：极大点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

4.Let $f(x)=\frac{\ln x}{x}$ ,where $x>0$ .
(a) Find the extreme value of $f(x)$ .
(b) Using the result of（a）,show that $e^{x} \geq x^{e}$ for $x>0$ .

#### 中文审定题干

设 $f(x)=\dfrac{\ln x}{x}$，其中 $x>0$。
(a) 求 $f(x)$ 的极值。
(b) 利用(a)的结果，证明对于 $x>0$，$e^x\ge x^e$。

#### 核验答案

(a) $f'(x)=(1-\ln x)/x^2$。当 $0<x<e$ 时 $f'(x)>0$，当 $x>e$ 时 $f'(x)<0$，故 $x=e$ 时取得最大值 $f(e)=1/e$。
(b) 对一切 $x>0$，由(a)得 $\ln x/x\le1/e$，即 $e\ln x\le x$。两边取指数得 $x^e\le e^x$；等号在 $x=e$ 时成立。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 5. `M2QD-DA-TRAIN-Q5`

- 原题号：TRAIN-Q5；分值：4；难度：Level 3。
- 主类型：最值与最优化；标签：极大点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=36 x^{2}+4 x^{3}-3 x^{4}$ .Find the greatest value of $f(x)$ .

#### 中文审定题干

定义 $f(x)=36x^2+4x^3-3x^4$。求 $f(x)$ 的最大值。

#### 核验答案

$f'(x)=-12x(x-3)(x+2)$，驻点为 $x=-2,0,3$。导数符号依次为 $+,-,+,-$，所以 $x=-2$ 和 $x=3$ 为极大点，且 $f(-2)=64$、$f(3)=189$。由于 $x\to\pm\infty$ 时 $f(x)\to-\infty$，故全局最大值为 $189$。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 6. `M2QD-DA-TRAIN-Q6`

- 原题号：TRAIN-Q6；分值：4；难度：Level 3。
- 主类型：最值与最优化；标签：极小点、区间最值、端点比较。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define \(f(x)=2x^{3}-3x^{2}-12x\), where \(x\geq-3\). Find the least value of \(f(x)\).

#### 中文审定题干

定义 $f(x)=2x^3-3x^2-12x$，其中 $x\ge-3$。求 $f(x)$ 的最小值。

#### 核验答案

$f'(x)=6(x-2)(x+1)$，驻点为 $x=-1,2$。在定义域 $[-3,\infty)$ 上，$f$ 先增、后减、再增；候选最小值为端点 $f(-3)=-45$ 与局部极小值 $f(2)=-20$。比较得全局最小值为 $-45$。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 7. `M2QD-DA-TRAIN-Q7`

- 原题号：TRAIN-Q7；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：拐点、凹凸性。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the continuous function $f(x)=\frac{x^{2}-1}{x^{2}+3}$ .Find all the point（s）of inflexion of the graph of $y=f(x)$ .

#### 中文审定题干

考虑连续函数 $f(x)=\dfrac{x^2-1}{x^2+3}$。求曲线 $y=f(x)$ 的所有拐点。

#### 核验答案

$f'(x)=8x/(x^2+3)^2$，$f''(x)=-24(x-1)(x+1)/(x^2+3)^3$。因此 $f''(x)=0$ 给出 $x=-1,1$；其符号在 $x=-1$ 处由负变正，在 $x=1$ 处由正变负，凹凸性均发生改变。又 $f(-1)=f(1)=0$，故全部拐点为 $(-1,0)$ 与 $(1,0)$。

#### 校订记录

- marks_total：题面未印分值，但出版社答案的分项标记合计6分且末行明确标示（6）。
- solution_original：题目要求点的坐标；只列函数值而不把横、纵坐标组成最终答案不完整。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 8. `M2QD-DA-TRAIN-Q8`

- 原题号：TRAIN-Q8；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：拐点、凹凸性。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

8.Let $y=\left(7 x+x^{2}\right) e^{-x}$ .
(a) Find $\frac{d y}{d x}$ and $\frac{d^{2} y}{d x^{2}}$ .
(b) Someone claims that there are two points of inflexion of the graph of $y=\left(7 x+x^{2}\right) e^{-x}$ . Do you agree？Explain your answer.

#### 中文审定题干

设 $y=(7x+x^2)e^{-x}$。
(a) 求 $dy/dx$ 及 $d^2y/dx^2$。
(b) 某人声称曲线 $y=(7x+x^2)e^{-x}$ 有两个拐点。你是否同意？解释你的答案。

#### 核验答案

(a) $dy/dx=(-x^2-5x+7)e^{-x}$，$d^2y/dx^2=(x^2+3x-12)e^{-x}$。
(b) 因 $e^{-x}>0$，二阶导数的零点为 $\alpha=(-3-\sqrt{57})/2$、$\beta=(-3+\sqrt{57})/2$，且其符号在两点外为正、两点之间为负，故两处均为拐点。因此同意该声称；两点可写成 $(\alpha,(7\alpha+\alpha^2)e^{-\alpha})$ 与 $(\beta,(7\beta+\beta^2)e^{-\beta})$。

#### 校订记录

- solution_original：保留两个相邻1M会令可见评分标记合计7分，与题面及答案总分6冲突。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 9. `M2QD-DA-TRAIN-Q9`

- 原题号：TRAIN-Q9；分值：3；难度：Level 2。
- 主类型：极值与曲线性质；标签：渐近线。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=\frac{4 x^{2}-5 x+1}{x+4}$ for all real numbers $x \neq-4$ .Find all the asymptotes of the graph of $y=f(x)$ .

#### 中文审定题干

对所有实数 $x\ne-4$，定义 $f(x)=\dfrac{4x^2-5x+1}{x+4}$。求曲线 $y=f(x)$ 的所有渐近线。

#### 核验答案

因分母在 $x=-4$ 为零而分子值为85，故垂直渐近线为 $x=-4$。多项式除法得 $f(x)=4x-21+85/(x+4)$，余项在 $x\to\pm\infty$ 时趋于0，故斜渐近线为 $y=4x-21$。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 10. `M2QD-DA-TRAIN-Q10`

- 原题号：TRAIN-Q10；分值：6；难度：Level 4。
- 主类型：极值与曲线性质；标签：渐近线、拐点、凹凸性。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

10.Define $r(x)=\frac{x^{3}-3 x^{2}+3 x+11}{(x-1)^{2}}$ for all real numbers $x \neq 1$ .
(a) Find the asymptote（s）of the graph of $y=r(x)$ .
(b) Find $\frac{d}{d x} r(x)$ .
(c) Find the number of point（s）of inflexion of the graph of $y=r(x)$ .

#### 中文审定题干

对所有实数 $x\ne1$，定义 $r(x)=\dfrac{x^3-3x^2+3x+11}{(x-1)^2}$。
(a) 求曲线 $y=r(x)$ 的渐近线。
(b) 求 $r'(x)$。
(c) 求曲线 $y=r(x)$ 的拐点数目。

#### 核验答案

先化为 $r(x)=x-1+12/(x-1)^2$。
(a) 垂直渐近线为 $x=1$，斜渐近线为 $y=x-1$。
(b) $r'(x)=1-24/(x-1)^3$。
(c) $r''(x)=72/(x-1)^4>0$（$x\ne1$），曲线在定义域各区间内均凹向上；$x=1$ 又不在定义域内，故没有拐点，数目为0。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 11. `M2QD-DA-TRAIN-Q11`

- 原题号：TRAIN-Q11；分值：8；难度：Level 4。
- 主类型：极值与曲线性质；标签：极大点、极小点、拐点、渐近线、曲线作图。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider a rational function $f(x)=\frac{x^{2}+6 x-3}{x-1}$ .It is given that
\begin{tabular}[t]{|l|l|l|l|l|l|l|l|}
\hline $x$ & $x<-1$ & －1 & $-1<x<1$ & 1 & $1<x<3$ & 3 & $x>3$ \\
\hline $f^{\prime}(x)$ & ＋ & 0 & － & undefined & － & 0 & ＋ \\
\hline $f^{\prime \prime}(x)$ & － & － & － & undefined & ＋ & ＋ & ＋ \\
\hline
\end{tabular}
（＇＋＇and＇－＇denote＇positive value＇and＇negative value＇respectively.）
(a) Find all the maximum and／or minimum point（s）of the graph of $y=f(x)$ ,and determine whether the graph of $y=f(x)$ has point（s）of inflexion.
(b) Find the asymptote（s）of the graph of $y=f(x)$ .
(c) Sketch the graph of $y=f(x)$ .

#### 中文审定题干

考虑有理函数 $f(x)=\dfrac{x^2+6x-3}{x-1}$。已知符号表各列依次为 $x<-1$、$x=-1$、$-1<x<1$、$x=1$、$1<x<3$、$x=3$、$x>3$；相应的 $f'(x)$ 符号为 $+$、$0$、$-$、未定义、$-$、$0$、$+$，$f''(x)$ 符号为 $-$、$-$、$-$、未定义、$+$、$+$、$+$。（“+”和“−”分别表示正值和负值。）
(a) 求曲线 $y=f(x)$ 的所有极大点及／或极小点，并判断曲线是否有拐点。
(b) 求曲线的渐近线。
(c) 描绘曲线。

#### 核验答案

(a) $f(-1)=4$、$f(3)=12$。由一阶导数变号，极大点为 $(-1,4)$，极小点为 $(3,12)$。二阶导数只在 $x=1$ 两侧变号，但 $x=1$ 不在定义域内，故没有拐点。
(b) $f(x)=x+7+4/(x-1)$，故垂直渐近线为 $x=1$，斜渐近线为 $y=x+7$。
(c) $x<1$ 的分支在斜渐近线下方，经过极大点 $(-1,4)$，并在 $x\to1^-$ 时趋于 $-\infty$；$x>1$ 的分支在斜渐近线上方，在 $x\to1^+$ 时趋于 $+\infty$，经过极小点 $(3,12)$ 后趋近 $y=x+7$。此描述与出版社图像一致。

#### 校订记录

- question_text_zh：原始MMD的引号及正负号被OCR破坏；输入记录已作语义正确的规范化，但未保存校订证据。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案及曲线图实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 12. `M2QD-DA-TRAIN-Q12`

- 原题号：TRAIN-Q12；分值：8；难度：Level 4。
- 主类型：极值与曲线性质；标签：极大点、极小点、拐点、渐近线、曲线作图。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider a rational function $f(x)=\frac{x^{2}+2}{x^{2}-1}$ .It is given that
\begin{tabular}[t]{|l|l|l|l|l|l|l|l|}
\hline $x$ & $x<-1$ & －1 & $-1<x<0$ & 0 & $0<x<1$ & 1 & $x>1$ \\
\hline $f^{\prime}(x)$ & ＋ & undefined & ＋ & 0 & － & undefined & － \\
\hline $f^{\prime \prime}(x)$ & ＋ & undefined & － & － & － & undefined & ＋ \\
\hline
\end{tabular}
（＇＋＇and＇－＇denote＇positive value＇and＇negative value＇respectively.）
(a) Find all the maximum and／or minimum point（s）of the graph of $y=f(x)$ ,and determine whether the graph of $y=f(x)$ has point（s）of inflexion.
(b) Find the asymptote（s）of the graph of $y=f(x)$ .
(c) Sketch the graph of $y=f(x)$ .

#### 中文审定题干

考虑有理函数 $f(x)=\dfrac{x^2+2}{x^2-1}$。已知符号表各列依次为 $x<-1$、$x=-1$、$-1<x<0$、$x=0$、$0<x<1$、$x=1$、$x>1$；相应的 $f'(x)$ 符号为 $+$、未定义、$+$、$0$、$-$、未定义、$-$，$f''(x)$ 符号为 $+$、未定义、$-$、$-$、$-$、未定义、$+$。（“+”和“−”分别表示正值和负值。）
(a) 求曲线 $y=f(x)$ 的所有极大点及／或极小点，并判断曲线是否有拐点。
(b) 求曲线的渐近线。
(c) 描绘曲线。

#### 核验答案

(a) $f(0)=-2$，一阶导数在 $x=0$ 由正变负，故极大点为 $(0,-2)$，没有极小点。二阶导数只在不属于定义域的 $x=\pm1$ 两侧变号，故没有拐点。
(b) 垂直渐近线为 $x=-1$、$x=1$；因 $f(x)=1+3/(x^2-1)$，水平渐近线为 $y=1$。
(c) 曲线为偶函数；两条外侧分支均在 $y=1$ 上方，靠近垂直渐近线时趋于 $+\infty$，当 $|x|\to\infty$ 时从上方趋近 $y=1$；内侧分支在 $x=\pm1$ 附近趋于 $-\infty$，并在 $(0,-2)$ 取得极大值。此描述与出版社图像一致。

#### 校订记录

- question_text_zh：原始MMD的引号及正负号被OCR误识为LaTeX符号；输入记录已规范化但未保存校订证据。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案及曲线图实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 13. `M2QD-DA-TRAIN-Q13`

- 原题号：TRAIN-Q13；分值：3；难度：Level 2。
- 主类型：变率；标签：相关变化率、体积变化。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

The volume $V \mathrm{~cm}^{3}$ of water in a glass is given by $V=\frac{\pi\left(h^{3}+3 h^{2}+3 h\right)}{12}(0 \leq h \leq 4)$ , where $h$ cm is the depth of water in the glass.Initially,the glass is full of water.There is a small hole at the bottom and water leaks out at a constant rate of $\pi \mathrm{cm}^{3} \mathrm{~s}^{-1}$ .Find the rate of change of the depth of water when the depth of water is 3 cm.

#### 中文审定题干

玻璃杯中水的体积 $V\,\mathrm{cm}^3$ 由 $V=\dfrac{\pi(h^3+3h^2+3h)}{12}$ 给出，其中 $0\le h\le4$，$h\,\mathrm{cm}$ 为水深。起初杯中装满水；杯底有一小孔，水以恒定速率 $\pi\,\mathrm{cm}^3\,\mathrm{s}^{-1}$ 漏出。求水深为 $3\,\mathrm{cm}$ 时水深的变化率。

#### 核验答案

$dV/dh=\pi(h+1)^2/4$，而漏水表示 $dV/dt=-\pi\,\mathrm{cm}^3\,\mathrm{s}^{-1}$。由链式法则 $dV/dt=[\pi(h+1)^2/4]dh/dt$。当 $h=3$ 时，$-\pi=4\pi\,dh/dt$，故 $dh/dt=-1/4\,\mathrm{cm}\,\mathrm{s}^{-1}$。负号表示水深下降。

#### 校订记录

- marks_total：题面未印分值，但出版社答案的分项标记合计3分且末行明确标示（3）。
- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

### 14. `M2QD-DA-TRAIN-Q14`

- 原题号：TRAIN-Q14；分值：5；难度：Level 3。
- 主类型：变率；标签：相关变化率、面积变化、建立变量关系。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=4 \ln x$ ,where $x>1$ .Let $O$ be the origin and $P$ be a point lying on $C$ .The vertical line which passes through $P$ cuts the $x$－axis at the point $Q$ .Denote the $x$－coordinate of $Q$ by $u$ .
(a) Express the area of $\triangle O P Q$ in terms of $u$ .
(b) If $P$ moves along $C$ such that $P Q$ decreases at a constant rate of 4 units per second, find the rate of change of the area of $\triangle O P Q$ when $u=e$ .

#### 中文审定题干

考虑曲线 $C:y=4\ln x$，其中 $x>1$。设 $O$ 为原点，$P$ 为 $C$ 上一点。过 $P$ 的竖直线与 $x$ 轴交于 $Q$，并以 $u$ 表示 $Q$ 的 $x$ 坐标。
(a) 用 $u$ 表示 $\triangle OPQ$ 的面积。
(b) 若 $P$ 沿 $C$ 移动，使 $PQ$ 以每秒4单位的恒定速率缩短，求当 $u=e$ 时 $\triangle OPQ$ 面积的变化率。

#### 核验答案

(a) $P=(u,4\ln u)$、$Q=(u,0)$，故面积 $A=\tfrac12(u)(4\ln u)=2u\ln u$ 平方单位。
(b) 令 $v=PQ=4\ln u$，则 $dv/dt=(4/u)du/dt$。已知 $dv/dt=-4$，所以当 $u=e$ 时 $du/dt=-e$。又 $dA/dt=(2+2\ln u)du/dt$，故在 $u=e$ 时 $dA/dt=-4e$ 平方单位每秒。

#### 校订记录

- solution_source_file/solution_source_member：当前成员只含题面，出版社答案实际来自甲部答案 MMD。
- solution_source_member_sha256：答案来源成员改为甲部答案MMD后，成员哈希必须同步改为该成员的SHA-256，才能保持来源追溯一致。

## 甲部特训（17题）

### 1. `M2QD-DA-PARTA-Q1`

- 原题号：PARTA-Q1；分值：4；难度：Level 2。
- 主类型：切线与法线；标签：已知切点求切线、隐函数求导。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $C$ be the curve $8 e^{x+y}=x^{2}+y^{2}$ .Find the equation of the tangent to $C$ at the point（2,－2）.

#### 中文审定题干

设 $C$ 为曲线 $8e^{x+y}=x^2+y^2$。求曲线 $C$ 在点 $(2,-2)$ 处的切线方程。（4分）

#### 核验答案

对曲线方程两边关于 $x$ 求导：$8e^{x+y}(1+\frac{dy}{dx})=2x+2y\frac{dy}{dx}$，故 $\frac{dy}{dx}=\frac{x-4e^{x+y}}{4e^{x+y}-y}$。在 $(2,-2)$ 处，切线斜率为 $-\frac13$，所以 $y+2=-\frac13(x-2)$，即 $x+3y+4=0$。

### 2. `M2QD-DA-PARTA-Q2`

- 原题号：PARTA-Q2；分值：4；难度：Level 3。
- 主类型：切线与法线；标签：与指定直线平行的切线、切点未知。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=x^{3}-4 x^{2}+8 x-7$ .Find the equations of the two tangents to the curve $C$ which are parallel to the line $L: 6 x-2 y+7=0$ . （4 marks）

#### 中文审定题干

考虑曲线 $C:y=x^3-4x^2+8x-7$。求曲线 $C$ 的两条与直线 $L:6x-2y+7=0$ 平行的切线方程。（4分）

#### 核验答案

$L$ 的斜率为 $3$。由 $y'=3x^2-8x+8=3$，得 $(3x-5)(x-1)=0$，故切点横坐标为 $1$ 或 $\frac53$。相应切点为 $(1,-2)$、$(\frac53,-\frac4{27})$。两条切线分别为 $y+2=3(x-1)$ 与 $y+\frac4{27}=3(x-\frac53)$，即 $3x-y-5=0$ 与 $81x-27y-139=0$。

### 3. `M2QD-DA-PARTA-Q3`

- 原题号：PARTA-Q3；分值：6；难度：Level 4。
- 主类型：切线与法线；标签：过指定点的切线、切点未知。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=\frac{16-4 x^{2}}{3+x^{2}}$ .Find the equations of the two tangents to the curve $C$ with $y$－intercept $\frac{13}{2}$ . （6 marks）

#### 中文审定题干

考虑曲线 $C:y=\frac{16-4x^2}{3+x^2}$。求曲线 $C$ 的两条 $y$ 截距均为 $\frac{13}{2}$ 的切线方程。（6分）

#### 核验答案

$y'=-\frac{56x}{(3+x^2)^2}$。设切点为 $(a,b)$，则切线通过 $(0,\frac{13}{2})$，所以 $\frac{b-13/2}{a}=-\frac{56a}{(3+a^2)^2}$，且 $b=\frac{16-4a^2}{3+a^2}$。消去 $b$ 得 $(a^2-1)^2=0$，故 $a=\pm1$，两切点均有纵坐标 $3$。在 $(1,3)$ 处斜率为 $-\frac72$，在 $(-1,3)$ 处斜率为 $\frac72$，故两条切线为 $7x+2y-13=0$ 与 $7x-2y+13=0$。

### 4. `M2QD-DA-PARTA-Q4`

- 原题号：PARTA-Q4；分值：3；难度：Level 2。
- 主类型：极值与曲线性质；标签：极大点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the continuous function $f(x)=x+2 \sin x$ ,where $0<x<2 \pi$ .Find all the maximum point（s）of the graph of $y=f(x)$ .

#### 中文审定题干

考虑连续函数 $f(x)=x+2\sin x$，其中 $0<x<2\pi$。求 $y=f(x)$ 图像上的所有极大点。（3分）

#### 核验答案

$f'(x)=1+2\cos x$。在 $0<x<2\pi$ 内，$f'(x)=0$ 给出 $x=\frac{2\pi}{3}$ 或 $x=\frac{4\pi}{3}$。导数在 $x=\frac{2\pi}{3}$ 两侧由正变负，故该处为极大点；在另一驻点两侧由负变正。所求极大点为 $(\frac{2\pi}{3},\frac{2\pi}{3}+\sqrt3)$。

### 5. `M2QD-DA-PARTA-Q5`

- 原题号：PARTA-Q5；分值：3；难度：Level 2。
- 主类型：极值与曲线性质；标签：极小点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the continuous function $f(x)=e^{2 x}-4 e^{x}+5$ .Find all the turning point（s）of the graph of $y=f(x)$ .

#### 中文审定题干

考虑连续函数 $f(x)=e^{2x}-4e^x+5$。求 $y=f(x)$ 图像上的所有转向点。（3分）

#### 核验答案

$f'(x)=2e^{2x}-4e^x=2e^x(e^x-2)$。因 $e^x>0$，唯一驻点为 $x=\ln2$。导数在该点两侧由负变正，且 $f(\ln2)=1$，故唯一转向点为极小点 $(\ln2,1)$。

### 6. `M2QD-DA-PARTA-Q6`

- 原题号：PARTA-Q6；分值：5；难度：Level 3。
- 主类型：最值与最优化；标签：区间最值、端点比较。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=x^{2} e^{-3 x}$ ,where $-1 \leq x \leq 1$ .Find the least value and the greatest value of $f(x)$ .

#### 中文审定题干

定义 $f(x)=x^2e^{-3x}$，其中 $-1\le x\le1$。求 $f(x)$ 的最小值及最大值。（5分）

#### 核验答案

$f'(x)=e^{-3x}x(2-3x)$，故区间内驻点为 $x=0$ 与 $x=\frac23$。比较驻点及端点：$f(-1)=e^3$、$f(0)=0$、$f(\frac23)=\frac4{9e^2}$、$f(1)=e^{-3}$。因此最小值为 $0$（在 $x=0$ 处取得），最大值为 $e^3$（在 $x=-1$ 处取得）。

#### 校订记录

- solution_original：题目同时要求最小值和最大值；来源答案虽已算出端点值，但缺少最大值结论。

### 7. `M2QD-DA-PARTA-Q7`

- 原题号：PARTA-Q7；分值：5；难度：Level 3。
- 主类型：最值与最优化；标签：区间最值、端点比较。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=x^{2} \ln x$ ,where $\frac{1}{2} \leq x \leq 1$ .Find the least value and the greatest value of $f(x)$ .

#### 中文审定题干

定义 $f(x)=x^2\ln x$，其中 $\frac12\le x\le1$。求 $f(x)$ 的最小值及最大值。（5分）

#### 核验答案

$f'(x)=x(1+2\ln x)$。在给定区间内，唯一驻点为 $x=e^{-1/2}$；导数在该点两侧由负变正，所以该处给出最小值 $f(e^{-1/2})=-\frac1{2e}$。再比较端点，$f(1)=0$，$f(\frac12)=\frac14\ln\frac12<0$，故最大值为 $0$（在 $x=1$ 处取得）。

### 8. `M2QD-DA-PARTA-Q8`

- 原题号：PARTA-Q8；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：拐点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Define $f(x)=\frac{k}{x^{2}-8 x+21}$ for all real numbers $x$ ,where $k$ is a constant.It is given that the extreme value of $f(x)$ is 1 .
(a) Find $f^{\prime}(x)$ .
(b) Does the graph of $y=f(x)$ have exactly two points of inflexion？Explain your answer.

#### 中文审定题干

对所有实数 $x$，定义 $f(x)=\frac{k}{x^2-8x+21}$，其中 $k$ 为常数。已知 $f(x)$ 的极值为 $1$。
(a) 求 $f'(x)$。
(b) $y=f(x)$ 的图像是否恰有两个拐点？解释你的答案。（6分）

#### 核验答案

因 $x^2-8x+21=(x-4)^2+5>0$，且极值为 $1$，有 $k\ne0$。$f'(x)=-\frac{k(2x-8)}{(x^2-8x+21)^2}$，其唯一驻点为 $x=4$；由 $f(4)=1$ 得 $k=5$，故 (a) $f'(x)=\frac{10(4-x)}{(x^2-8x+21)^2}$。(b) $f''(x)=\frac{10(3x^2-24x+43)}{(x^2-8x+21)^3}$，其零点为 $x=4\pm\frac{\sqrt{15}}3$（约 $2.71,5.29$）。分母恒正而分子在两根外为正、两根间为负，故 $f''$ 在两处均变号；图像恰有两个拐点。

### 9. `M2QD-DA-PARTA-Q9`

- 原题号：PARTA-Q9；分值：7；难度：Level 3。
- 主类型：极值与曲线性质；标签：极大点、极小点、渐近线。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

It is given that the graph of $y=A x+\frac{1}{x+B}$ intersects the $x$－axis at the point $(1,0)$ and has the vertical asymptote $x=2$ ,where $A$ and $B$ are constants.Find the local extreme point（s）and the other asymptote（s）of the graph.

#### 中文审定题干

已知 $y=Ax+\frac1{x+B}$ 的图像与 $x$ 轴相交于点 $(1,0)$，且有垂直渐近线 $x=2$，其中 $A,B$ 为常数。求该图像的局部极值点及其他渐近线。（7分）

#### 核验答案

垂直渐近线 $x=2$ 给出 $B=-2$。代入 $(1,0)$ 得 $A=1$，故 $y=x+\frac1{x-2}$。当 $x\to\pm\infty$ 时 $\frac1{x-2}\to0$，所以另一条渐近线为 $y=x$。$y'=1-\frac1{(x-2)^2}$，驻点横坐标为 $1,3$。导数在 $x=1$ 两侧由正变负、在 $x=3$ 两侧由负变正，因此局部极大点为 $(1,0)$，局部极小点为 $(3,4)$。

### 10. `M2QD-DA-PARTA-Q10`

- 原题号：PARTA-Q10；分值：6；难度：Level 3。
- 主类型：极值与曲线性质；标签：极大点、极小点、拐点、曲线作图。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

10.Let $f(x)=(2-x)(x-8)^{2}$ .
(a) Find the turning point（s）and the point（s）of inflexion of the graph of $y=f(x)$ .
(b) Sketch the graph of $y=f(x)$ for $0 \leq x \leq 10$ .

#### 中文审定题干

设 $f(x)=(2-x)(x-8)^2$。
(a) 求 $y=f(x)$ 图像上的所有转向点及拐点。
(b) 描绘 $0\le x\le10$ 时 $y=f(x)$ 的图像。（6分）

#### 核验答案

(a) $f'(x)=-3(x-4)(x-8)$。导数符号依次为负、正、负，故 $(4,-32)$ 为极小点，$(8,0)$ 为极大点。又 $f''(x)=-6(x-6)$ 在 $x=6$ 处变号，故拐点为 $(6,-16)$。(b) 图像从端点 $(0,128)$ 下降，经过 $(2,0)$ 后到 $(4,-32)$；继而上升，经拐点 $(6,-16)$ 到 $(8,0)$（在此与 $x$ 轴相切）；之后下降到 $(10,-32)$。区间 $[0,6)$ 凹向上，$(6,10]$ 凹向下。

### 11. `M2QD-DA-PARTA-Q11`

- 原题号：PARTA-Q11；分值：7；难度：Level 4。
- 主类型：极值与曲线性质；标签：渐近线、拐点、曲线作图。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

11.Define $f(x)=\frac{m x+n}{2 x-1}$ for all real numbers $x \neq \frac{1}{2}$ ,where $m$ and $n$ are non－zero constants. Denote the graph of $y=f(x)$ by $C$ .It is given that the $y$－intercept of $C$ is -9 and $y+4=0$ is a horizontal asymptote of $C$ .
(a) Find the other asymptote（s）of $C$ .
(b) Prove that $f(x)$ is decreasing.
(c) Prove that $C$ does not have any points of inflexion.
(d) Sketch $C$ .

#### 中文审定题干

对所有实数 $x\ne\frac12$，定义 $f(x)=\frac{mx+n}{2x-1}$，其中 $m,n$ 均为非零常数。将 $y=f(x)$ 的图像记为 $C$。已知 $C$ 的 $y$ 截距为 $-9$，且 $y+4=0$ 是 $C$ 的水平渐近线。
(a) 求 $C$ 的其他渐近线。
(b) 证明 $f(x)$ 为递减函数。
(c) 证明 $C$ 没有拐点。
(d) 描绘 $C$。（7分）

#### 核验答案

(a) 分母为零时 $x=\frac12$，故其他渐近线为 $x=\frac12$。(b) 由 $f(0)=-9$ 得 $n=9$；水平渐近线为 $y=\frac m2=-4$，故 $m=-8$。于是 $f(x)=\frac{-8x+9}{2x-1}$，且 $f'(x)=-\frac{10}{(2x-1)^2}<0$，所以在定义域的两个区间上均递减。(c) $f''(x)=\frac{40}{(2x-1)^3}$，在定义域内不为零；唯一不定义处 $x=\frac12$ 不在曲线上，故没有拐点。(d) 图像的渐近线为 $x=\frac12,y=-4$，经过 $(0,-9)$ 并在 $(\frac98,0)$ 穿过 $x$ 轴；左支位于 $y=-4$ 下方并递减至 $-\infty$，右支由 $+\infty$ 递减并从上方趋近 $y=-4$。

### 12. `M2QD-DA-PARTA-Q12`

- 原题号：PARTA-Q12；分值：7；难度：Level 4。
- 主类型：变率；标签：相关变化率、几何量变化、面积变化、体积变化、建立变量关系。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

A container in the form of an inverted right circular cone is held vertically.The height and the slant height of the container are 32 cm and 40 cm respectively.Initially,the container is full of water.Then,water is leaked from the apex of the conical container.
(a) Let $A \mathrm{~cm}^{2}$ be the wet curved surface area of the container and $h$ cm be the depth of water in the container.Express $A$ in terms of $h$ .
(b) The volume of water in the container decreases at a constant rate of $9 \pi \mathrm{~cm}^{3} / \mathrm{s}$ .Find the rate of change of the wet curved surface area of the container when the depth of water in the container is 2 cm.

#### 中文审定题干

一倒置的直圆锥形容器竖直放置，其高和斜高分别为 $32\text{ cm}$ 和 $40\text{ cm}$。起初容器盛满水，随后水从圆锥顶点漏出。
(a) 设 $A\text{ cm}^2$ 为容器被水浸湿的曲面面积，$h\text{ cm}$ 为水深。以 $h$ 表示 $A$。
(b) 容器内水的体积以恒定速率 $9\pi\text{ cm}^3/\text{s}$ 减少。求水深为 $2\text{ cm}$ 时，被浸湿曲面面积的变率。（7分）

#### 核验答案

由勾股定理，容器底面半径为 $24\text{ cm}$。相似圆锥给出水面半径 $r=\frac34h$、水的斜高 $l=\frac54h$。(a) $A=\pi rl=\frac{15}{16}\pi h^2$。(b) 水体积 $V=\frac13\pi r^2h=\frac3{16}\pi h^3$，故 $\frac{dV}{dt}=\frac9{16}\pi h^2\frac{dh}{dt}$。当 $h=2$ 且 $\frac{dV}{dt}=-9\pi$ 时，$\frac{dh}{dt}=-4\text{ cm/s}$。又 $\frac{dA}{dt}=\frac{15}{8}\pi h\frac{dh}{dt}$，所以所求变率为 $-15\pi\text{ cm}^2/\text{s}$。

### 13. `M2QD-DA-PARTA-Q13`

- 原题号：PARTA-Q13；分值：4；难度：Level 3。
- 主类型：极值与曲线性质；标签：从基本原理求导、导数为正区间。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=\frac{1}{x}+x$ .
(a) Find $\frac{d y}{d x}$ from first principles.
(b) Find the range of values of $x$ when the slope of tangent to $C$ is positive.

#### 中文审定题干

考虑曲线 $C:y=\frac1x+x$。
(a) 从基本原理求 $\frac{dy}{dx}$。
(b) 求曲线 $C$ 的切线斜率为正时 $x$ 的取值范围。（4分）

#### 核验答案

定义域为 $x\ne0$。(a) 由基本原理，$\frac{dy}{dx}=\lim_{h\to0}\frac{[\frac1{x+h}+x+h]-[\frac1x+x]}h=\lim_{h\to0}\left(1-\frac1{x(x+h)}\right)=1-\frac1{x^2}$。(b) 要求 $1-\frac1{x^2}>0$，即 $\frac{(x-1)(x+1)}{x^2}>0$。因 $x^2>0$，故 $x<-1$ 或 $x>1$。

#### 校订记录

- solution_original：题目明确要求从基本原理求导；只列初始差商没有完成推导或回答。

### 14. `M2QD-DA-PARTA-Q14`

- 原题号：PARTA-Q14；分值：5；难度：Level 2。
- 主类型：极值与曲线性质；标签：极小点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $f(x)$ be a continuous function defined on $\mathbf{R}$ .It is given that the graph of $y=f^{\prime}(x)$ is a straight line with $x$－intercept -8 and $y$－intercept 6 .
(a) Find the slope of the tangent to the curve $y=f(x)$ at $x=2$ .
(b) Find the $x$－coordinate（s）of all the turning point（s）of the curve $y=f(x)$ .For each turning point,determine whether it is a minimum point or a maximum point.

#### 中文审定题干

设 $f(x)$ 为定义在 $\mathbb R$ 上的连续函数。已知 $y=f'(x)$ 的图像是一条直线，其 $x$ 截距为 $-8$，$y$ 截距为 $6$。
(a) 求曲线 $y=f(x)$ 在 $x=2$ 处的切线斜率。
(b) 求曲线 $y=f(x)$ 所有转向点的 $x$ 坐标，并分别判定为极小点还是极大点。（5分）

#### 核验答案

直线 $y=f'(x)$ 通过 $(-8,0)$ 与 $(0,6)$，故 $f'(x)=\frac34x+6$。(a) 切线斜率为 $f'(2)=\frac{15}{2}$。(b) $f'(x)=0$ 只有 $x=-8$。又 $f''(x)=\frac34>0$，故该转向点为极小点，其 $x$ 坐标为 $-8$。

### 15. `M2QD-DA-PARTA-Q15`

- 原题号：PARTA-Q15；分值：8；难度：Level 4。
- 主类型：极值与曲线性质；标签：切点未知、拐点、凹凸性。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $g(x)$ be a continuous function defined on $\mathbf{R}^{+}$,where $\mathbf{R}^{+}$is the set of positive real numbers.It is given that $g^{\prime}(x)=\frac{4 x^{2}-5 x+36}{x}$ for all $x>0$ .
(a) Is $g(x)$ an increasing function？Explain your answer.
(b) Denote the curve $y=g(x)$ by $G$ .It is given that $P(p, 0)$ is the point of inflexion of $G$ . Let $L$ be the tangent to $G$ at $P$ .
(i) Find the equation of $L$ .
(ii) By considering $g^{\prime \prime}(x)$ ,explain why $G$ lies above $L$ in the interval $(p, \infty)$ .

#### 中文审定题干

设 $g(x)$ 为定义在正实数集 $\mathbb R^+$ 上的连续函数。已知对所有 $x>0$，$g'(x)=\frac{4x^2-5x+36}{x}$。
(a) $g(x)$ 是否为递增函数？解释你的答案。
(b) 将曲线 $y=g(x)$ 记为 $G$。已知 $P(p,0)$ 为 $G$ 的拐点，设 $L$ 为 $G$ 在 $P$ 处的切线。
(i) 求 $L$ 的方程。
(ii) 通过考察 $g''(x)$，解释为什么在区间 $(p,\infty)$ 内 $G$ 位于 $L$ 上方。（8分）

#### 核验答案

(a) 对 $x>0$，$g'(x)=\frac{4(x-5/8)^2+551/16}{x}>0$，故 $g$ 为递增函数。(b) $g'(x)=4x-5+\frac{36}{x}$，所以 $g''(x)=4-\frac{36}{x^2}$。在正实数域内，$g''$ 只在 $x=3$ 为零，且由负变正，故 $p=3$。(i) $P=(3,0)$ 且 $g'(3)=19$，所以 $L:y=19(x-3)=19x-57$。(ii) 在 $(3,\infty)$ 内 $g''(x)>0$，曲线 $G$ 凹向上，因此该区间内曲线位于其在 $P$ 处的切线 $L$ 上方。

### 16. `M2QD-DA-PARTA-Q16`

- 原题号：PARTA-Q16；分值：9；难度：Level 4。
- 主类型：极值与曲线性质；标签：渐近线、极小点、拐点。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let \(f(x)=\frac{(x+5)^3}{(x-2)^2}\) for all real numbers \(x\ne2\). Denote the graph of \(y=f(x)\) by \(H\).

(a) Find the asymptote(s) of \(H\).

(b) Find \(f^{\prime}(x)\).

(c) Find the turning point(s) of \(H\).

(d) Find the point(s) of inflexion of \(H\).

#### 中文审定题干

对所有实数 $x\ne2$，设 $f(x)=\frac{(x+5)^3}{(x-2)^2}$，并将 $y=f(x)$ 的图像记为 $H$。
(a) 求 $H$ 的渐近线。
(b) 求 $f'(x)$。
(c) 求 $H$ 的转向点。
(d) 求 $H$ 的拐点。（9分）

#### 核验答案

(a) 垂直渐近线为 $x=2$。多项式除法给出 $f(x)=x+19+\frac{147}{x-2}+\frac{343}{(x-2)^2}$，故斜渐近线为 $y=x+19$。(b) $f'(x)=\frac{(x+5)^2(x-16)}{(x-2)^3}$。(c) 驻点横坐标为 $-5,16$；$f'$ 在 $x=-5$ 两侧不变号，在 $x=16$ 两侧由负变正，故唯一转向点为极小点 $(16,\frac{189}{4})$。(d) $f''(x)=\frac{294(x+5)}{(x-2)^4}$，在 $x=-5$ 两侧由负变正，且 $f(-5)=0$，故唯一拐点为 $(-5,0)$。

#### 校订记录

- question_text_original：来源答案(b)实际求 $f'(x)$，且(c)明确写“By (b), we have $f'(x)=...$”；若(b)要求 $f''$，题答与后续引用均不成立。
- question_text_zh：与英文疑点相同；应使中文题干与可验证的题答链一致。
- solution_original：题目要求拐点而非只求横坐标；答案缺少最终坐标结论。

### 17. `M2QD-DA-PARTA-Q17`

- 原题号：PARTA-Q17；分值：8；难度：Level 4。
- 主类型：综合微分应用；标签：相关变化率、面积变化、链式法则建模、建立变量关系、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Consider the curve $C: y=\ln x$ ,where $x>1$ .Let $P$ be a moving point lying on $C$ .The tangent to $C$ at $P$ cuts the $x$－axis at the point $Q$ .
(a) Denote the $x$－coordinate of $P$ by $r$ .Find the coordinates of $Q$ in terms of $r$ .
(b) Let $O$ be the origin.It is given that $O P$ increases at a constant rate of 2 units per minute.Find,correct to 3 significant figures,the rate of change of the area of $\triangle O P Q$ when the $x$－coordinate of $P$ is $\sqrt{e}$ .

#### 中文审定题干

考虑曲线 $C:y=\ln x$，其中 $x>1$。设 $P$ 为 $C$ 上的动点，曲线 $C$ 在 $P$ 处的切线与 $x$ 轴相交于点 $Q$。
(a) 以 $r$ 表示 $P$ 的 $x$ 坐标，求 $Q$ 的坐标，答案以 $r$ 表示。
(b) 设 $O$ 为原点。已知 $OP$ 以每分钟 $2$ 个单位的恒定速率增加。求当 $P$ 的 $x$ 坐标为 $\sqrt e$ 时，$\triangle OPQ$ 面积的变率，答案准确至三位有效数字。（8分）

#### 核验答案

(a) $P=(r,\ln r)$，切线斜率为 $1/r$。设 $Q=(a,0)$，则 $\frac{-\ln r}{a-r}=\frac1r$，故 $Q=(r-r\ln r,0)$。(b) $OP=\sqrt{r^2+(\ln r)^2}$，所以 $\frac{d(OP)}{dt}=\frac{r^2+\ln r}{r\sqrt{r^2+(\ln r)^2}}\frac{dr}{dt}$。在 $r=\sqrt e$ 时令左边为 $2$，可得 $\frac{dr}{dt}=\frac{2\sqrt e\sqrt{e+1/4}}{e+1/2}$。此时 $Q$ 的横坐标为正，面积 $A=\frac12r(1-\ln r)\ln r$，故 $\frac{dA}{dr}=\frac12[1-\ln r-(\ln r)^2]$。代入 $r=\sqrt e$ 得 $\frac{dA}{dt}=\frac{\sqrt{4e^2+e}}{4(2e+1)}\approx0.221$ 平方单位/分钟。

## 乙部特训（6题）

### 1. `M2QD-DA-PARTB-Q1`

- 原题号：PARTB-Q1；分值：13；难度：Level 4。
- 主类型：极值与曲线性质；标签：驻点、极大点、极小点、一阶导数判别法、拐点、渐近线、曲线作图、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $f(x)=\frac{x^{4}}{x^{3}+2}$ ,where $x \neq-2^{\frac{1}{3}}$ .
(a) Find the $x$－and $y$－intercept（s）of the graph of $y=f(x)$ .
(b) Find $f^{\prime}(x)$ and prove that $f^{\prime \prime}(x)=\frac{12 x^{2}\left(4-x^{3}\right)}{\left(x^{3}+2\right)^{3}}$ .
(c) （i）For the graph of $y=f(x)$ ,find all the extreme point（s）and point（s）of inflexion.
(ii) Find all the asymptote（s）of the graph of $y=f(x)$ .
(iii) Sketch the graph of $y=f(x)$ .

#### 中文审定题干

设 $f(x)=\frac{x^{4}}{x^{3}+2}$，其中 $x\ne-2^{1/3}$。
(a) 求曲线 $y=f(x)$ 与 $x$ 轴及 $y$ 轴的截距。（1分）
(b) 求 $f'(x)$，并证明 $f''(x)=\frac{12x^{2}(4-x^{3})}{(x^{3}+2)^{3}}$。（4分）
(c) (i) 求曲线 $y=f(x)$ 的所有极值点及拐点；(ii) 求所有渐近线；(iii) 描绘曲线。（8分）

#### 核验答案

(a) 两个截距均对应点 $(0,0)$。
(b) $f'(x)=\frac{x^{3}(x^{3}+8)}{(x^{3}+2)^{2}}$，再次求导得 $f''(x)=\frac{12x^{2}(4-x^{3})}{(x^{3}+2)^{3}}$。
(c)(i) $f'(x)=0$ 给出 $x=-2,0$。由一阶导数符号，极大点为 $(-2,-8/3)$，极小点为 $(0,0)$。$f''$ 在垂直渐近线 $x=-2^{1/3}$ 两侧异号，但该点不在定义域；在定义域内，$f''$ 于 $x=2^{2/3}$ 处改变符号，故唯一拐点为 $(2^{2/3},2^{5/3}/3)$；$x=0$ 不是拐点。(ii) 垂直渐近线为 $x=-2^{1/3}$；由 $f(x)=x-\frac{2x}{x^{3}+2}$，斜渐近线为 $y=x$。(iii) 草图应显示上述渐近线、极值点、拐点，并在 $x=-2^{1/3}$ 两侧分别趋于 $-\infty$ 与 $+\infty$。

#### 校订记录

- solution_original：冻结来源文本存在重复及错位，无法直接作为教师答案使用；现有材料不足以进一步断言错误发生于原版还是转换阶段。
- question_text_zh：统一DSE书面表达并使分值结构完整。

### 2. `M2QD-DA-PARTB-Q2`

- 原题号：PARTB-Q2；分值：14；难度：Level 4。
- 主类型：极值与曲线性质；标签：渐近线、曲线作图、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Let $C_{1}$ be the curve $y=\frac{p x+q}{2 x+r}$ ,where $p, q$ and $r$ are constants with $p \neq 0$ and $x \neq-\frac{r}{2}$ . It is given that $C_{1}$ passes through $(0,0)$ and it has a vertical asymptote $x=-\frac{3}{2}$ and a horizontal asymptote $y+1=0$ .Let $C_{2}$ be the curve $y=\frac{2 x+r}{p x+q}$ ,where $x \neq-\frac{q}{p}$ .
(a) Find the equation of $C_{1}$ .
(b) Find the coordinates of the point（s）of intersection of $C_{1}$ and $C_{2}$ .
(c) Show that $\frac{d}{d x}\left(\frac{p x+q}{2 x+r}\right)<0$ for $x \neq-\frac{r}{2}$ and $\frac{d}{d x}\left(\frac{2 x+r}{p x+q}\right)>0$ for $x \neq-\frac{q}{p}$ .
(d) Write down all the asymptotes of $C_{2}$ .
(e) Sketch the curves $C_{1}$ and $C_{2}$ on the same diagram,indicating their asymptotes, intercepts and their point（s）of intersection.

#### 中文审定题干

设 $C_1$ 为曲线 $y=\frac{px+q}{2x+r}$，其中 $p,q,r$ 为常数、$p\ne0$ 且 $x\ne-r/2$。已知 $C_1$ 经过 $(0,0)$，垂直渐近线为 $x=-3/2$，水平渐近线为 $y=-1$。另设 $C_2$ 为曲线 $y=\frac{2x+r}{px+q}$，其中 $x\ne-q/p$。
(a) 求 $C_1$ 的方程。（4分）
(b) 求 $C_1$ 与 $C_2$ 的交点。（2分）
(c) 证明在各自定义域内，$\frac{d}{dx}(\frac{px+q}{2x+r})<0$ 且 $\frac{d}{dx}(\frac{2x+r}{px+q})>0$。（3分）
(d) 写出 $C_2$ 的所有渐近线。（2分）
(e) 在同一坐标系中描绘 $C_1$ 与 $C_2$，标明渐近线、截距及交点。（3分）

#### 核验答案

(a) 由经过原点得 $q=0$；垂直渐近线给出 $r=3$；水平渐近线给出 $p/2=-1$，故 $p=-2$，$C_1:y=-2x/(2x+3)$。
(b) $C_2:y=(2x+3)/(-2x)$。联立两式得唯一交点 $(-3/4,1)$。
(c) $C_1'=-6/(2x+3)^2<0$（$x\ne-3/2$）；$C_2'=3/(2x^2)>0$（$x\ne0$）。
(d) $C_2$ 的垂直渐近线为 $x=0$，水平渐近线为 $y=-1$。
(e) 草图应显示：$C_1$ 的两截距均为原点，渐近线 $x=-3/2,y=-1$；$C_2$ 的 $x$ 截距为 $(-3/2,0)$、无 $y$ 截距，渐近线 $x=0,y=-1$；两曲线交于 $(-3/4,1)$，且分别单调递减、单调递增。

#### 校订记录

- question_text_zh：改善中文语法而不改变数学条件。
- solution_original：冻结来源存在重复行且草图仅以图片呈现；清理后教师答案可独立阅读和核对。现有材料不足以进一步判断这些现象发生于原版还是转换阶段。

### 3. `M2QD-DA-PARTB-Q3`

- 原题号：PARTB-Q3；分值：13；难度：Level 4。
- 主类型：极值与曲线性质；标签：驻点、极大点、极小点、一阶导数判别法、拐点、渐近线、曲线作图、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

3.Let $f(x)=x-\frac{x}{x+1}$ ,where $x \neq-1$ .
(a) Find $f^{\prime}(x)$ and $f^{\prime \prime}(x)$ ,where $x \neq-1$ .
(b) （i）Find the relative extreme point（s）of the graph of $y=f(x)$ .
(ii) Show that the graph of $y=f(x)$ does not have any point of inflexion.
(c) Find the asymptote（s）of the graph of $y=f(x)$ .
(d) Sketch the graph of $y=f(x)$ .

#### 中文审定题干

设 $f(x)=x-\frac{x}{x+1}$，其中 $x\ne-1$。
(a) 求 $f'(x)$ 及 $f''(x)$。（2分）
(b) (i) 求曲线 $y=f(x)$ 的所有局部极值点；(ii) 证明曲线没有拐点。（6分）
(c) 求曲线的所有渐近线。（2分）
(d) 描绘曲线。（3分）

#### 核验答案

(a) $f'(x)=1-1/(x+1)^2$，$f''(x)=2/(x+1)^3$。
(b)(i) $f'(x)=0$ 给出 $x=-2,0$。由一阶导数符号，局部极大点为 $(-2,-4)$，局部极小点为 $(0,0)$。(ii) $f''(x)=0$ 无解；虽然凹凸性在 $x=-1$ 两侧改变，但 $f(-1)$ 无定义，故没有拐点。
(c) 由 $f(x)=x-1+1/(x+1)$，垂直渐近线为 $x=-1$，斜渐近线为 $y=x-1$。
(d) 草图应显示上述两条渐近线及两个局部极值点，并符合各区间的单调性与凹凸性。

#### 校订记录

- question_text_zh：采用更常见且清晰的DSE数学术语，并补回小问分值。
- solution_original：图片中的函数标签与题目不一致；图形形状、渐近线和极值点对应正确函数。
- solution_original：冻结来源文本不能直接复用；另将草图中的错误函数标签独立记录。

### 4. `M2QD-DA-PARTB-Q4`

- 原题号：PARTB-Q4；分值：13；难度：Level 5。
- 主类型：变率；标签：相关变化率、几何量变化、链式法则建模、隐函数求导、建立变量关系、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Figure 1 shows a rail $A O B$ with $\angle A O B=\frac{2 \pi}{3}$ and $A O$ lying on the horizontal plane.$A$ rod $M N$ of length 14 m is connected to the centres of two identical spheres of radius $\sqrt{3} \mathrm{~m}$ . The two spheres are free to slide on the rail and they touch $O A$ and $O B$ at $P$ and $Q$ respectively.It is given that the points $A, B, O, P, Q, M$ and $N$ lie on the same vertical plane.Let $O P=x \mathrm{~m}$ and $O Q=y \mathrm{~m}$ .
(a) Show that $\frac{d y}{d x}=-\frac{2 x+y-3}{x+2 y-3}$ .
(b) The sphere with centre $N$ is moving towards $O$ at a constant speed of $2 \mathrm{~m} \mathrm{~s}^{-1}$ and the angle between the rod $M N$ and the horizontal plane is $\theta$（in radians）.When $x=11$ , find the rate of increase of $\theta$ .

#### 中文审定题干

图1所示的轨道 $AOB$ 满足 $\angle AOB=2\pi/3$，且 $AO$ 位于水平面上。长 $14\,\mathrm{m}$ 的棒 $MN$ 连接两个半径均为 $\sqrt3\,\mathrm{m}$ 的相同球体的球心。两球可沿轨道自由滑动，并分别与 $OA$、$OB$ 相切于 $P$、$Q$。点 $A,B,O,P,Q,M,N$ 位于同一竖直平面内。设 $OP=x\,\mathrm{m}$、$OQ=y\,\mathrm{m}$。
(a) 证明 $\frac{dy}{dx}=-\frac{2x+y-3}{x+2y-3}$。（4分）
(b) 以 $N$ 为球心的球体以 $2\,\mathrm{m\,s^{-1}}$ 的恒定速率移向 $O$。设棒 $MN$ 与水平面的夹角为 $\theta$（弧度）。当 $x=11$ 时，求 $\theta$ 的增加率。（9分）

#### 核验答案

由球的半径及几何关系可得三角形两边为 $x-1$、$y-1$，夹角为 $2\pi/3$。余弦定理给出 $x^2+y^2+xy-3x-3y=193$。
(a) 对 $x$ 求导：$2x+2y\,dy/dx+y+x\,dy/dx-3-3\,dy/dx=0$，故 $dy/dx=-(2x+y-3)/(x+2y-3)$。
(b) 当 $x=11$ 时，关系式给出 $y=7$。球心 $N$ 移向 $O$，所以 $dx/dt=-2$，从而 $dy/dt=(-13/11)(-2)=26/11$。由正弦定理，$y=1+\frac{28}{\sqrt3}\sin\theta$；当 $y=7$ 时，$\sin\theta=3\sqrt3/14$、$\cos\theta=13/14$。求导并代入得 $d\theta/dt=\sqrt3/11\,\mathrm{rad\,s^{-1}}$。

#### 校订记录

- question_text_zh：改善术语、语法与单位书写，不改变数学条件。

### 5. `M2QD-DA-PARTB-Q5`

- 原题号：PARTB-Q5；分值：12；难度：Level 5。
- 主类型：综合微分应用；标签：区间最值、几何最优化、相关变化率、面积变化、链式法则建模、建立变量关系、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

The curve $y=1-x^{2}$ intersects the horizontal line $y=k$（where $0<k<1$ ）at two points $P$ and $Q$ .Let $O$ be the origin.
(a) Express the area of $\triangle O P Q$ in terms of $k$ .
(b) Find the greatest area of $\triangle O P Q$ .
(c) It is given that $O P$ increases at a rate of 2 units per second.Find the rate of change of the area of $\triangle O P Q$ when the $y$－coordinate of $P$ is $\frac{1}{3}$ .
(d) A student guesses that when the area of $\triangle O P Q$ attains its greatest value,$O P$ will also attain its greatest value.Explain whether the student＇s guess is correct or not.

#### 中文审定题干

曲线 $y=1-x^2$ 与水平线 $y=k$（$0<k<1$）相交于 $P,Q$ 两点，$O$ 为原点。
(a) 用 $k$ 表示 $\triangle OPQ$ 的面积。（3分）
(b) 求 $\triangle OPQ$ 的最大面积。（3分）
(c) 已知 $OP$ 以每秒2单位的速率增加。当 $P$ 的 $y$ 坐标为 $1/3$ 时，求 $\triangle OPQ$ 面积的变化率。（4分）
(d) 某学生猜想：当 $\triangle OPQ$ 的面积达到最大值时，$OP$ 也达到最大值。说明该猜想是否正确。（2分）

#### 核验答案

(a) $P,Q$ 的横坐标为 $\pm\sqrt{1-k}$，故面积 $A=k\sqrt{1-k}$。
(b) $dA/dk=(2-3k)/(2\sqrt{1-k})$，在 $0<k<1$ 上于 $k=2/3$ 取得最大值 $2\sqrt3/9$。
(c) $OP=\sqrt{k^2-k+1}$。由 $d(OP)/dt=2$ 得 $dk/dt=\frac{2\sqrt{k^2-k+1}}{2k-1}\cdot2$。当 $k=1/3$ 时，$dA/dt=-\sqrt{42}$ 平方单位/秒。
(d) 在面积最大时 $k=2/3$，但 $d(OP)/dk=\frac{2k-1}{2\sqrt{k^2-k+1}}\ne0$，故 $OP$ 当时并非极值，猜想不正确。

#### 校订记录

- solution_original：由(a)的底乘高直接得到，且后一行导数与后续结果也对应此正确表达式；冻结MMD明确呈现错误式，但现有材料不足以进一步断言错误发生于原版还是转换阶段。现数据库答案已使用正确式但此前未保存校订记录。
- question_text_zh：统一简体中文书面表达并完整呈现分值。

### 6. `M2QD-DA-PARTB-Q6`

- 原题号：PARTB-Q6；分值：13；难度：Level 5。
- 主类型：综合微分应用；标签：几何最优化、相关变化率、几何量变化、链式法则建模、建立变量关系、综合题目。
- 来源：`M2Quick Drill-微分法的应用.mmd.zip` / `ab3a3800-3b11-4cb8-af40-46ce05caf9f6.mmd`。

#### 英文原题

Denote the graph of $y=-\sqrt{x^{2}+4}$ and the graph of $y=\sqrt{(x-10)^{2}+9}$ by $G$ and $H$ respectively,where $0<x<10$ .Let $P$ be a moving point on $G$ .The vertical line passing through $P$ cuts $H$ at the point $Q$ .Denote the $x$－coordinate of $P$ by $p$ .It is given that the length of $P Q$ attains its minimum value when $p=a$ .
(a) Find $a$ .
(b) （i）Someone claims that the area of $\triangle O P Q$ attains its minimum value when $p=a$ . Do you agree？Explain your answer.
(ii) The length of $O P$ increases at a constant rate of 2 units per second.Find the rate of change of the perimeter of $\triangle O P Q$ when $p=a$ .

#### 中文审定题干

将曲线 $y=-\sqrt{x^2+4}$ 与 $y=\sqrt{(x-10)^2+9}$ 的图像分别记为 $G,H$，其中 $0<x<10$。点 $P$ 在 $G$ 上移动，过 $P$ 的竖直线与 $H$ 相交于 $Q$。设 $P$ 的横坐标为 $p$。已知当 $p=a$ 时，$PQ$ 的长度取得最小值。
(a) 求 $a$。（4分）
(b) (i) 有人声称当 $p=a$ 时，$\triangle OPQ$ 的面积也取得最小值。你是否同意？说明理由；(ii) $OP$ 以每秒2单位的恒定速率增加，求当 $p=a$ 时 $\triangle OPQ$ 周长的变化率。（9分）

#### 核验答案

(a) $PQ=\sqrt{(p-10)^2+9}+\sqrt{p^2+4}$。令导数为0并利用 $0<p<10$，得 $p=4$，故 $a=4$。
(b)(i) 面积 $A=\frac12p\,PQ$。在 $p=4$ 时 $d(PQ)/dp=0$，但 $dA/dp=PQ/2=5\sqrt5/2\ne0$，所以不同意。(ii) $OP=\sqrt{2p^2+4}$；在 $p=4$ 且 $d(OP)/dt=2$ 时，$dp/dt=3/2$。又 $OQ=\sqrt{p^2+(p-10)^2+9}$。设周长为 $w=OP+OQ+PQ$，则在 $p=4$ 时 $d(PQ)/dp=0$、$d(OQ)/dp=-2/\sqrt{61}$，故 $dw/dt=2-3/\sqrt{61}=2-3\sqrt{61}/61$ 单位/秒。

#### 校订记录

- question_text_zh：使用更自然、统一的简体数学表达。
