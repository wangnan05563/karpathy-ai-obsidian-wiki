# HUNDSUN票据交易管理平台软件V5.0-前端开发指导

恒生电子股份有限公司

票据交易管理平台V5.0

前端开发指导

# 准备工作

## 前端开发介绍

### vue介绍

vue.js 就是一款前端javascript框架，具体描述详见官网

官网：https://cn.vuejs.org/

特点，高效、易用、灵活

### h-ui介绍

hui是我们公司研发中心jres团队在基于vue.js上开发一款ui组件产品；主要是对常用组件，页面布局，以及相应的主题，详见参照官网

官网：http://192.168.58.189:8080/hui/#/

主要是方便了业务开发，不需要从零开始去封装写常用组件.

### ES6语法介绍

ES6是ECMAScript （欧洲计算机制造商协会/Ecmma国际）定义的JavaScript语言的标准，定义JavaScript语言的语法，语义，以及相应的标准，把控性能等；建议学习可参照业内人士阮一峰《ECMAScript 6 入门》一书

网址：http://es6.ruanyifeng.com/#README

## 环境安装运行

### node安装

安装node.js，打包依赖的环境，下面这个是windows安装包，若是其他环境到官网下载https://nodejs.org/en/download/ 下载安装包运行，一直下一步，安装完毕，现今，安装node会直接自带安装所运行环境依赖的python。接着可以验证node是否安装成功。

确定node 安装成功$ node –v, 如果指令不生效，检查下系统环境变量是否有node安装目录（安装node自动添加的）  如果有环境变量不行的话重启系统

### Python安裝

可以通过 python官网https://www.python.org/downloads/windows/下载对应版本的python安装包或直接使用以下版本

安装结束后 检查是否安装成功

打开命令行窗口界面（开始->运行->输入cmd），输入python --version，若出现python 版本号，则表示安装成功

若安装时没有选择自动添加到环境变量，请配置

### 安装淘宝镜像

因为在运行node环境所需依赖三方包在外网无法下载，所以需要安装淘宝镜像使用命令执行$ npm install -g cnpm --registry=https://registry.npm.taobao.org 。测试是否安装成功 $ cnpm –v

## 项目运行

1)进入到本地前端项目$bemp/ frontend 目录下执行npm install或cnpm install 来下载程序运行所需的三方依赖库。

2)执行npm run dll 命令，对资源文件的过滤

3)在当前目录$bemp/ frontend 下执行 npm run dev 即会跳出浏览器运行效果。

## 内存溢出

执行npm install cross-env -save-dev && npm install increase-memory-limit -save-dev

修改package.json里scripts的fix-memory-limit的内存大小，LIMIT指定分配的内存大小

执行npm run fix-memory-limit，只需执行一次即可，然后重新启动项目

# 工程结构介绍

## 前端目录说明

使用git的命令行窗口，执行Git clone $bemp/ frontend 下载前端项目源码。（git未安装需要先安装git）。当然也可客户端下载。

1)api.编写js文件

2)assets 存放图标文件

3)components 开发公用自定义组件

4)views 开发界面文件

5)store 项目状态仓库

6)sysconfig.js 请求数据的后台地址

## 后台模块分类

## 前端模块与后台模块相对应

Sm 系统公共

Pc  功能组件

Shcpe票交所对接

Ce  对公交易

Be  同业交易

Bm 业务管理

Pb  公共业务

Pl  票据池

## 菜单路径规则

/功能系统模块/子模块/具体业务/视图  如

=》 系统公共/权限管理/机构管理/机构管理员页面

=》 /sm/auth/branch/branchAdmin

注意：切勿创建错误，错误后会找不到视图

# 页面开发

## 页面结构

页面布局是常用的内容管理系统的结构，上左右

上：系统状态栏

左：菜单列表

右：工作区管理(主要是：1、查询表单，2、操作按钮，3、数据列表，4、分页栏)

如下图：

## 开发介绍

### 查询表单代码

代码说明

1)表单布局结构不能改变，页面上的dom节点样式class必须保证拼写无误

<div class="h-form-search-box">

<h-panel class="clearfix" :class="{'h-form-overhd':!ifShowMore}">

<h-form :model="formItem" :label-width="90" ref="formItem" cols="4" class="h-form-search">

2) 表单上需要在js里的data属性定义的变量：formItem: 绑定表单输入域值

3) ifshowMore ：是否显示高级查询

4) label属性名设置为 :label-width = “90”

5) 表单输入域name : prop =”brchNo”

<h-form-item label="机构号" prop="brchNo">

6) 查询表单校验：只控制输入长度maxlength=”20”

7) 表单触发按钮触发事件

<h-button type="primary" @click="formSearch()">{{$t("m.i.common.search")}}</h-button>

<h-button type="ghost" @click="formSearchReset()">{{$t("m.i.common.reset")}}</h-button>

<script>

formSearch() { //触发表单查询数据，并渲染响应到列表中

this.$refs.datagrid.dataChange(1);

},

formSearchReset() { // 清空表单输入域数据

this.$refs.formItem.resetFields();

},

</script>

8) 注意：表单输入域如果超出3个，应添 “高级”按钮

### 操作按钮

#### 按钮代码

#### 对应按钮事件

按钮触发时间脚本代码应写在js/ methods:{}

2-3.3 列表数据通过 配置gridData属性获取数据

定义 gridData变量，在触发事件、或初始化发送请求获取数据

#### 新增处理

新增

handleAddForm(str) {

this.type = str;

this.readonly = false;

this.isRequired = true;

this.addForm.userId = null;

if (this.type == "modify" || this.type == "view") {

if (this.currentSelectRow.length === 0) {

this.$hMessage.info(this.$t("m.i.common.chooseOneData"));

return;

}

let newRow = this.currentSelectRow[0];

this.addForm.userNo = newRow.userNo;

this.addForm.userId = newRow.userId;

this.addForm.userName = newRow.userName;

this.addForm.brchNo = newRow.brchNo;

this.addForm.brchName = newRow.brchName;

this.addForm.userRemark = newRow.userRemark;

this.addForm.phoneNo = newRow.phoneNo;

if (this.type == "modify") {

if (newRow.operateStatus === "UH00") {

this.$hMessage.info("该柜员正在复核中，请重新选择");

return;

}

this.readonly = true;

}

if (this.type == "view") {

this.addForm.relOrg = this.currentSelectRow.org_name;

this.addForm.kindCode = this.currentSelectRow.kind_name;

this.addForm.beginDateFmt = this.currentSelectRow.begin_date_fmt;

this.addForm.endDateFmt = this.currentSelectRow.end_date_fmt;

this.isRequired = false;

}

} else {

this.addFormReset();

}

this.addOrEditWin = true;

},

弹出框新增编辑表单

#### 表单说明

有相同父元素的子元素必须有独特的 key，重复的 key 会造成渲染错误。

常见用例：

结合 v-for使用：

form表单需要通过v-if动态控制字段显隐

2)新增编辑表单数据绑定 :model=”addForm”

3)注意：弹出框布局with 控制 400, 800，1000，支持最大化maximize = true

提交表单

submitForm() {

let btnType = this.type;

this.$refs["addForm"].validate(valid => {

if (valid) {

let url = this.type === "modify" ? this.reqUrl + "/updateBranchUser" : this.reqUrl + "/addBranchUser";

let msg = this.type === "modify" ? this.$t("m.i.common.modifySuccess") : this.$t("m.i.common.addSuccess");

this.submitFlag = true;

post(this.addForm, url).then(res => {

this.submitFlag = false;

if (res) {

let return_code = res.data.return_code;

if (res.data.retCode === "000000") {

this.$hMessage.success(msg);

this.addOrEditWin = false;

this.$refs.datagrid.dataChange(1);

this.currentSelectRow = [];

this.currentSelectList = [];

} else {

this.$hMessage.error(this.$t("m.i.common.addFailed") + res.data.retMsg);

this.$refs.datagrid.dataChange(1);

}

} else {

this.$hMessage.error(this.$t("m.i.common.netError"));

}

});

}

});

},

### 数据列表

数据列表为封装成的表格组件：数据表格和分页

# 通用组件

每个页面即都为组件，可供项目任何页面调用。

页面（父组件）调用其他页面（子组件）为组件通信。

调用组件步骤：

在脚本中引入被调组件 import aExample from xxx/xxx/x/aExmaple.vue

在componet中注册 components:{ aExmaple }

在页面中使用< a-example >  </ a-example >

如下例子：

引入机构树组件

<h-form-item label="机构号" prop="brchNo">

<h-input v-model="formItem.brchNo" readonly icon="android-search"

@on-click="queryBrchNo('query')"></h-input>

</h-form-item>

查看组件的可引用的组件$sm/auth/branch/showBranch.vue

## 文件批量导入CommonFileUpload

界面如下

调用方式

入参

## 打印凭证

系统所用通过模板设计后打印凭证的处理：先新增模板并设计，后的各个业务调用打印服务。

凭证模板新增：选择对应的业务打印类型，关联产品

凭证模板设计：在新增模板后进行根据需求设计打印模板（注意：设计模板只能通过ie浏览器来设计模板）

凭证打印调用：凭证打印所实现的js文件见 ./utils/print/LodopFun.js,可根据不同的业务需求进行修改，和新增实现

调用this.$print.vochPrint(this,options);

Options ：{params :voucher, callback:()=>{}, errorCallback: ()=>{} ,…..} 可扩展。

注意：配置打印模板时

1、需要同时打印内容和清单的，可根据实际情况设置占位符billList的高度；清单数较多存在分页的情况下，需在模板添加“Offset2Top”属性，表示次页开始的上边距偏移量（整数或字符型，可声明单位或百分比，负数表示向上偏移，正数表示向下偏移）；示例如下：

LODOP.ADD_PRINT_TEXT(373,50,100,"60%","billList");

LODOP.SET_PRINT_STYLEA(0,"Offset2Top","-28%");

## 记账分录展示acctRecord

### 显示分录

1）调用方式

传参：

param：调用后台获取分录服务的传参

url: 调用后台获取分录服务的url

submitFlag: 控制点击分录页面确定记账时的提交中灰显

showPrintButton: 控制确定记账后是否显示打印按钮 （不需要打印则不需要传该参数）

showAcctRecordWin: 控制打开和关闭分录弹窗

回调方法：

acctSubmitSure()：确定记账方法

showAcctRecordWinClose(): 关闭分录弹窗方法

printSuccessCallback(): 打印成功回调方法

可参考：acptAccountMain页面

### 不显示分录自动记账

具体调用方式与4.3.1显示分录一致，改动点如下：

改造原有代码的acctSubmitSure方法：返回参数新增callback，记账报错时需新增此回调函数，示例如下：

分录配置：根据is_ignore属性控制记账时是否展示分录，配置分录时在<acct_tran>节点新增is_ignore属性，并设为1，通过业务管理子系统-账务管理-分录管理-导入分录界面，重新导入配置好的分录，并刷新分录数据缓存。

可参考页面：src/views/bizViews/banks/sdnxbank/pl/iopool/common/ioPoolAccountBill.vue

# 前端统一风格

## 查询表单

1）主界面表单的label-width为“90”，弹出框的label-width为“115”

主界面：

弹窗：

2）弹出框宽度 定为400,800,1000宽度

400为一列的布局表单

800为两列布局表单

1000为三列布局表单或列表管理页面

3）弹出框按钮 名为 “确定”、“关闭”

## 列表按钮

样式都为 type=”primary”

<h-button type="primary" @click="roleDistribute()">角色分配</h-button>

<h-button type="primary" @click="showMenu()">查看菜单</h-button>

<h-button type="primary" @click="handleStatus()">用户状态</h-button>

<h-button type="primary" @click="handleOffLine()">置为离线</h-button>

## 字段使用

字典统一采用公共js提供方法获取

注意：字典功能正常使用，必须在基于字典表数据存在且正确的前提前，在使用common中字典相关方法前，请务必确认自己所需的数据，已经真实存在于字典表中，且与代码中定义相同。

CommonUtil中，主要提供三个方法。

3.1getDictListByGroups【根据组编号查询得到字典信息】

使用示例：

如图，该方法可以通过组编号，将一个或多个组下的所有字典信息全部查询出来。

建议在页面生命周期函数mounted中使用，获取到所有select需要的List，并且得到一个map对象，map中包括这些组编号下的所有字典信息。

3.2getDictValueFromMap【从map中获取dict对象】

该方法可以从3.1中获取到的map里，根据group和key获取得到所想要的value值，并且相关判断已写好，若查询字典得到的值为空，则会返回原本的key。

使用示例：

如图，在data的columns中，通过getDictValueFromMap方法，取得对应groupCode，key下的value值。

3.3getDictValueByKey【根据组编号和key值获取某个指定key的value值（不推荐使用）】

用法与3.1类似，通过groupCode和key，获取某一行指定的，字典表的值。

如图，该方法每次都会调用后台获取数据，因此在需要查询多个key对应的value值时，效率会非常低下，故如无必要，不推荐使用。3.1和3.2就足以应对大多数情况。

3.4 应用说明

注意：字典功能正常使用，必须在基于字典表数据存在且正确的前提前，在使用common中字典相关方法前，请务必确认自己所需的数据，已经真实存在于字典表中，且与代码中定义相同。

按照以下步骤配置，即可使用

在mounted生命周期函数中，查询得到所需要字典组下的信息，赋给select需要的List，和页面后期获取字典数据需要的map。

相应效果：

在columns中，根据字典map获取key对应的value值，并通过render显示到grid列表中。

注意，这里要使用span，用div会导致ellipsis:true的省略效果失效

相应效果：

## 列表相关

详细用法请见“HUNDSUN票据交易管理平台软件V5.0-组件使用说明文档.docx”；

表格：分为单选和多选，由columns中设置的radio和selection属性决定。

单选：                              多选：

单选：请设置onCurrentChange和onCurrentChangeCancel事件，进行赋值和取消操作。

多选：

1、不支持翻页勾选，设置onSelectChange事件进行赋值；

2、支持翻页勾选，不需要额外添加事件，并根据以下属性取值：

this.$refs.datagrid.selects（选中的记录集）

this.$refs.datagrid.selectIds（选中的记录Id集）

在重新查询或新增等操作响应成功后，应去掉组件记录数据，将selects和selectIds置为[]

this.$refs.datagrid.selects = [];
this.$refs.datagrid.selectIds = [];

注意：单选时，若使用onRowClick事件，能正常进行赋值，但无法取消赋值，且只有在选中行时才能触发该事件，若只选中单选框原点，则不会触发。

如果返回列不存在id，需设置一个paramId，作为多选时的唯一主键

## 时间格式化

1、日期为字符串，调用方式如下：

this.$moment(“20181219”, "YYYY-MM-DD").format("YYYY-MM-DD");

this.$moment(“122334”, "HH:mm:ss").format("HH:mm:ss");建议使用以下提供的formatTime方法

this.$moment(“20181219122334”,"YYYY-MM-DD HH:mm:ss").format("YYYY-MM-DD HH:mm:ss");

注意：年月日可直接使用this.$moment(“20181219”).format("YYYY-MM-DD")进行格式化，若存在时分秒，须使用this.$moment(“122334”, "HH:mm:ss")；

2、日期为时间戳，调用方式如下：

this.$moment(1411641720000).format("YYYY-MM-DD HH:mm:ss");

this.$moment(1411641720000).format("YYYY-MM-DD");

this.$moment(1411641720000).format("HH:mm:ss");

3、时间格式化formatTime（不足6位时会先不足）

此方法在调用this.$moment(“122334”, "HH:mm:ss").format("HH:mm:ss")前加了一层判断时间是否为6位的判断，不足时自动补全，建议使用该方法。

示例：

1）引入：import {  formatTime  } from "@/api/bizApi/commonUtil";

2）调用：let transTm = formatTime(“22334”);

## 金额格式化

使用前引入格式化函数:

import {formatNumber} from "@/api/bizApi/commonUtil";

使用方法:

num为需格式化的金额字符串,返回格式化后的字符串

formatNumber(num, 2, ',')

## 输入框

输入框提示，

规则：当明眼就能看得懂地段标签就知道输入内容的就不用提示；

搜索查询赋值的都不提供提示；

若输入需要有格式的给出格式；

若输入内容未知，给出提示；

如图：

输入框在表单提交或失去焦点时的校验应遵循规则

请求响应提示

响应成功：this.$msgTip.success(this,{info:’’})

提交提示：this.$msgTip.warn(this,{info:’’})

响应失败：this.$msgTip.error(this,{info:’’})

信息提示：this.$msgTip.info(this,{info:’’})

## 菜单权限拦截

机构员管理菜单

/sm/auth/branch/branchAdmin

此页面上的请求应在加一层

如：新增 /sm/auth/branch/branchAdmin/saveBranch

删除 /sm/auth/branch/branchAdmin/deleteBranch

。。。。。

## 清空条件选择输入值

在业务页面中表单查询有条件选择输入域，为了方便查询提供单独清除输入值的图标。只要点击，并带有回调方法进行去除表单属性值。

<h-form-item label="保证增信行" prop="guarntrTrustBankName">
<h-input v-model="formItem.guarntrTrustBankName" placeholder=" " readonly
icon="android-search" @on-click="queryCpesBrchCode('move')" clearable @on-clear="clearVal('move')"></h-input>
</h-form-item>

方法回调：

methods:{

….

clearVal(){

//清空表单对应属性

this.formItem.guarntrTrustBrchCode = "";

this.formItem.guarntrTrustBankName = "";

},

……

}

## 弹窗初始化调用

调用<h-msg-box>组件时，如果存在使用$refs属性对弹框中定义的控件进行调用的情况，先显示弹窗，并在this.$nextTick(() => {});方法中调用，不然会出现控件未定义的错误。示例如下：

this.billCreditWin = true;

this.$nextTick(() => {
  this.$refs.billCreditDatagrid.dataChange(1);

this.addForm.id = "";

this.$refs.addForm.resetFields();
});

## 清单导出

清单导出时，调用@/api/bizApi/commonUtil的exportList方法，传入参数说明如下：

代码示例如下：

## 弹窗样式

查询表单和表格同时存在时，<h-msg-box>标签添加h-form-table-layer样式，<h-form>标签前不需要额外添加<h-panel>标签

其他情况下，<h-msg-box>标签添加h-form-search-layer样式

## 票面样式

票面信息显示字数过长时，可添加label-multi-long-label样式，示例如下

## 报表通用方法

开发报表时，调用@/api/bizApi/commonUtil的reportFunc方法，包含方法及入參说明如下：

可参考rinanceBillBusiStatisticsReportOne界面，代码示例如下：

## 文件下载（报错时弹窗提示）

使用时，调用@/api/bizApi/commonUtil的fileDownload方法，包含方法及入參说明如下：

代码示例如下：

import { fileDownload } from "@/api/bizApi/commonUtil";

fileDownload(this,

"/be/market/quote/trackQuery/func_exportDealSale",

{
  downloadMethod: 'post',
  paramsByPost: {
    id: this.$refs.datagrid.selectIds
  }
});

注：文件名需要从后台获取时，需要在开发接口时添加如下代码：

response.setHeader("Access-Control-Expose-Headers", "Content-Disposition");

# 个性化登录界面改造

以山东农信个性化登录界面为例，配置参数bemp.hs_cust_name=sdnxbank：

新建个性化登录界面login.vue，放在views/bizViews/banks/sdnxbank下

在src/api/loginIndex.js添加个性化登录界面入口

访问方式：根据sysconfig.js的isCustomLogin进行控制

isCustomLogin为默认值false：不自动进行跳转，仍显示产品登录界面；若需要访问个性化登录界面，可通过http://127.0.0.1:8091/#/sdnxbank/login 进行访问

isCustomLogin设为true：可通过产品登录地址http://127.0.0.1:8091/#/login直接跳转至个性化登录界面

# 个性化首页改造

以重庆银行为例，配置参数bemp.hs_cust_name=cqbank：

首页共分为四个模块，对应下图四个展示区域，可对此分别进行个性化改造。

个性化首页配置：在src/api/bank/mainIndex路径下新增“xxx”MainIndex.js文件，“xxx”与bemp.hs_cust_name参数值保持一致，在该文件下添加个性化首页模块路径，key保持不变，改变webpackChunkName和对应菜单路径即可，设置webpackChunkName时，需將路径中的bank改为banks，如下图：

# 路由映射配置

## 菜单路径配置

配置文件目录：src/api/index.js;

配置说明：key :()=>import(/*webpackChunkName:“${key}”*/`@ views/bizViews/${key}.vue`)

注意：只需在配置文件目录下配置相应菜单入口即可，界面中引用的组件采用动态组件加载的方式，无需体现在此js中，webpackChunkName中的key开头不允许存在“/”

如图：

如果发现页面空白，设置文件里的name名称与组件vue同名

并修改index里的配置

## 审批路径配置

业务模块对应的审批界面配置在src/api/auditFlow.js文件下，如下图：

## 凭证打印路径配置

业务模块对应的凭证打印界面配置在src/api/printUrl.js文件下，如下图：

## 个性化菜单路径配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化菜单路径配置：在src/api/bank路径下新增“xxx”Index.js文件，“xxx”与bemp.hs_cust_name参数值保持一致，在该文件下添加个性化菜单入口，key保持不变，改变webpackChunkName和对应菜单路径即可，如下图：

## 个性化审批路径配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化审批路径配置：在src/api/bank/auditFlow路径下新增“xxx”AuditFlow.js文件，“xxx”与bemp.hs_cust_name参数值保持一致，在该文件下添加个性化审批菜单入口，key保持不变，改变webpackChunkName和对应菜单路径即可，如下图：

## 个性化凭证打印路径配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化菜单路径配置：在src/api/bank/printUrl路径下新增“xxx”PrintUrl.js文件，“xxx”与bemp.hs_cust_name参数值保持一致，在该文件下添加个性化凭证打印菜单入口，key保持不变，改变webpackChunkName和对应菜单路径即可，如下图：

## 个性化组件配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化组件配置：在src/components/bank路径下新增“xxx”文件夹及对应index.js，“xxx”与bemp.hs_cust_name参数值保持一致，index.js用于动态注册个性化组件，参照src/components/bemp/index.js即可，新添加的个性化组件名称与产品组件名称保持一致，如下图：

## 个性化样式配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化样式配置：在src/views/bizViews/banks路径下新增“xxx/style”文件夹及对应style.scss，“xxx”与bemp.hs_cust_name参数值保持一致，style.scss内定义需要个性化的样式，最外层样式需定义为“.${bemp.hs_cust_name}”，如bemp.hs_cust_name=“zdcfinance”，则定义为“.zdcfinance{ }”，需要个性化的样式嵌套在.zdcfinance内。个性化样式写法参照src/style/local/style.scss即可，如下图：

若需要个性化图片路径，可将其放在src/assets/xxx文件夹下，示例路径如下：

## 个性化国际化文件配置

个性化银行：以配置中心参数bemp.hs_cust_name决定

个性化国际化文件配置：在views/bizViews/banks/路径下新增“xxx/locale/lang”文件夹，并拷贝static/locale/lang目录下的zh-CN.js文件至该路径下即可，“xxx”与bemp.hs_cust_name参数值保持一致。

# 页面组件化开发

常用字段可单独封装一个组件，不常用字段可使用封装的通用组件，一个页面业务上的输入域都通过引入组件来渲染。

已封装组件可看

组件封装与使用：

eg: 封装通用下拉框组件commonSelect.vue；源码请看项目代码。

在开发业务页面引用：

<common-select v-model="formItem.tradeRange" :label="$t('m.i.be.tradeRange')" prop="tradeRange" :dictList="tradeRangeList"></common-select>

# 按钮显隐控制

以电票质押申请为例，隐藏“删除”按钮、新增弹窗下“删除”按钮

1、提供按钮权限脚本，格式如下：

insert into TM_BUTTON_AUTH (ID, AUTH_ID, BTN_PATH, BTN_LEVEL, PARENT_AUTH_NO, BTN_SHOW_FLAG, CREATE_TIME, UPDATE_TIME, RESERVE1, RESERVE2, RESERVE3)
values (1, 404020102, '/impawnDelete', 1, null, '0', null, null, null, null, null);
insert into TM_BUTTON_AUTH (ID, AUTH_ID, BTN_PATH, BTN_LEVEL, PARENT_AUTH_NO, BTN_SHOW_FLAG, CREATE_TIME, UPDATE_TIME, RESERVE1, RESERVE2, RESERVE3)
values (2, 404020102, '/impawnAdd/impawnBillDelete', 2, null, '0', null, null, null, null, null);

注：AUTH_ID：菜单权限ID，与TM_AUTHORITY中的ID对应

BTN_PATH：按钮路径，用于控制按钮显隐，可嵌套，根据“/”进行分级

如“/impawnAdd/impawnBillDelete”：表示隐藏新增质押申请界面的删除按钮

2、在mounted下根据当前菜单ID调用接口“/sm/auth/buttonAuth/func_queryButtonByAuthId”获取按钮权限，示例如下：

let id = JSON.parse(window.sessionStorage.getItem("curMenu")).id;
post({ authId: id }, "/sm/auth/buttonAuth/func_queryButtonByAuthId").then(res => {
  if (res) {
    let retCode = res.data.retCode;
    let retMsg = res.data.retMsg;
    if (retCode === "000000") {
      this.btnAuth = JSON.parse(res.data.retData);
    } else {
      this.$msgTip.error(this, { info: retMsg });
    }
  } else {
    this.$msgTip.error(this, { info: this.$t("m.i.common.netError") });
  }
});

后台返回数据格式如下：

{
  "authId": 404020102,	//菜单权限ID
  "impawnDelete": {		//菜单页面对应按钮ID，控制主页面按钮的显隐
     "isShow": false
   },
  "impawnAdd": {
    "isShow": true,
    "children": {
      "impawnBillDelete": {
        "isShow": false
       }
    }
  }
}

3、按钮权限控制：

质押申请界面：

新增质押申请：

# 前端易现缺陷

## IE下界面打开后空白，谷歌正常

### 异常分析

出现此现象的原因是在界面开发时，同一个标签下使用了多个相同属性，导致在IE的严格模式下报错，如下图，当同时存在两个readonly属性时，IE界面打开时就会空白

### 改进措施

添加属性时先看下改属性是否存在，开发完成后同时在谷歌和IE下都测试一下。

## 查询条件显示

### 异常分析

开发时不够细心，查询条件未超出3个时仍添加了高级按钮，导致点击高级按钮时无反应；条件少于3个时未将“查询”、“重置”按钮靠左展示

### 改进措施

测试时多关注下界面展示细节。

目前界面查询条件不超过3个时不需要添加高级选项，且条件少于3个时，请添加one-form或two-form样式，如下图：

## 弹窗界面表单显示问题

### 表单和表格同时存在

#### 异常分析

小屏正常显示，但大屏下，部分弹框界面会出现以下输入框特别小的现象，如图1，主要原因是在弹窗的form表单前添加了<h-panel>标签，如图2

图1

图2

#### 改进措施

正确写法：<h-msg-box>标签添加h-form-table-layer样式，<h-form>标签前不需要额外添加<h-panel>标签

### 只存在表单项

#### 异常分析

弹框界面出现以下输入框特别小的现象，如图1，主要原因是<h-msg-box>标签添加的是h-form-table-layer样式，而不是h-form-search-layer

#### 改进措施

正确写法：<h-msg-box>标签添加h-form-search-layer样式

注意点：当同时存在表单和表格时，弹窗样式为h-form-table-layer，只存在表单时，弹出样式为h-form-search-layer

## 数据重置

### 查询条件重置

#### 异常分析

情况一：form表单属性未定义，调用表单的resetFields方法后，因为设置的prop属性，该字段被被重置为undefined

情况二：存在日期区间、票据金额最大最小等区间取值时，未将所有值全部置空

#### 改进措施

开发时注意检查是否所有用到字段均已初始化；

写重置方法时，除了调用表单的resetFields外，把已赋值且不包含在prop属性内的字段，手动置空

### 窗口关闭后数据未清空

#### 异常分析

如企业客户维护，新增和修改公用一个弹出窗口

1、场景一：点击新增弹出新增窗口，输入数据后点击关闭，再次打开新增界面，数据未清空

原因：关闭事件只对窗口的显隐做了控制，并未对表单数据进行清空操作或在界面重新打开时未进行数据重置

2、场景二：先点击修改弹出修改窗口，反显数据，关闭窗口后打开新增界面，显示上一次修改反显的数据

原因：未将新增时的数据重置和修改时数据赋值操作放在$nextTick事件内

#### 改进措施

方式一：在关闭窗口时，先对数据进行重置操作

方式二：每次打开窗口前，根据当前事件类型，做不同处理。新增时，先对form表单进行数据重置；修改时，对form表单进行赋值操作；需将这两步操作放入$nextTick事件内

## 弹窗无法打开

### 异常分析

情况一：定义data时，使用了未定义的字段，控制台报错

情况二：弹窗首次创建时，弹窗内的组件实例尚未被创建，此时通过refs调用组件方法就会报错

### 改进措施

定义data属性时要注意不要重复定义或调用未初始化的变量；

打开弹窗时若需要调用组件内部的方法，请先将控制弹窗显隐的属性置为true，组件调用方法放入$nextTick事件中

## 多选框无法选中多条数据

### 异常分析

表格多选的情况下，选中多条数据默认是以ID作为唯一主键，当请求返回的数据不存在ID这个字段时，便会出现无法选中多条的情况

### 改进措施

开发时注意一下返回请求数据是否存在ID列，不存在时需设置paramId属性作为自定义的唯一主键

## 表单标签名称太长时出现省略号

### 异常分析

超过6个字符时文本出现省略号，未添加换行样式"h-form-long-label"

### 改进措施

超过6个文本时请添加换行样式class="h-form-long-label"

## 文本域显示问题

### 异常分析

未添加自适应高度样式"h-form-height-auto"

### 改进措施

使用文本域时，请添加自适应高度样式class="h-form-height-auto"

## 日期控件位于最右侧时显示不全

### 异常分析

日期选择器出现位置默认值为bottom-start，导致日期控件位于最右侧时显示不全，如下图：

### 改进措施

已全局设置h-date-picker组件的autoPlacement属性为true，让日期面板方向自适应，不需要额外添加；

若要指定日期面板的出现方向，请先将autoPlacement设为false

## 明细界面详情栏数据不显示

### 异常分析

批次明细两个界面切换，且明细界面的详情栏作为组件动态引入，首次从批次进入明细界面时，详情栏组件未被初始化，无法调用内部的查询方法，导致第一次进入时详情栏显示为空

### 改进措施

将对详情栏组件数据的查询放在该组件的mounted内进行调用

## 页签切换时界面会重新刷新

### 异常分析

页面名称不一致，导致缓存失效

### 改进措施

创建新页面时注意名称要保持一致

## 分页栏未在最底部显示

### 异常分析

对表格设置了指定高度，分页栏没有显示在底部，表格没有自适应高度

### 改进措施

需求没有特别说明，使用表格组件时不需要额外设置高度

## 弹框内的表格放大后宽度没有自适应

### 异常分析

缺少弹框最大化事件，对表格进行刷新操作

### 改进措施

弹窗添加on-maximize事件，点击最大化时对表格进行刷新

## 日期格式化错误

### 异常分析

后台返回的时间长度不为6时，如91234，此时调用this.$moment进行格式化时错误

### 改进措施

调用commonUtil内的formatTime方法，将不足6位的时间补全至6位后再进行格式化

## 利率校验规则

### 异常分析

控制利率范围为0-100时，正则表达式有误，输入1000或10000000等也能校验通过，原因是未对“.”进行转义

错误正则表达式：

### 改进措施

修改正则表达式，对“.”进行转义（后续推荐使用金额组件）
