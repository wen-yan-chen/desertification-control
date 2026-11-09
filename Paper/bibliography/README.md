# 论文文献库

`references.bib` 收录 Reference 中的 48 项资料：REF01–REF16 为原有 PDF／网页，CN01–CN16 为中文论文，EN01–EN16 沿用英文补充库原有引用键。数据集入口、方法论文和不同论文独立保留；不是重复拷贝原始资料。

## 正文引用

```tex
\cite{REF01}
\cite{REF03,EN02}
\cite{CN01}
```

正文入口已经加载此库，使用 XeLaTeX + BibTeX（安装完整 TeX Live / MacTeX）：

```sh
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error Paper/main.tex
```

LaTeX Workshop 使用 latexmk 配方时会自动调用 BibTeX。手动编译则在 Paper 内依次运行 `xelatex main`、`bibtex main`、`xelatex main`、`xelatex main`。

当前 `Section/references.tex` 中启用了 `\nocite{*}`，便于检查全部 48 项。正式论文只列实际引用资料时，删除或注释这一行，正文 `\cite{...}` 引用的条目会自动保留。编号自动生成，不要手填 `[1]`。

## 题录来源与待核验项

- 原有文献依照资料索引及本地 PDF 首页整理；REF07–REF10 引用本地 arXiv 版本，REF10 使用 v2 的 2022 年。
- 英文补充文献沿用原有 `references.bib`；原库的内部核验说明保存在 `annotation` 字段，不作为正式引用文字输出。本次仅转换整理，没有重新联网核验全部题录。
- **CN01–CN16 来自本地《文献可用之处说明.docx》，仍属待核验题录。** 已保留原记录中的作者、刊名、年期，卷号、页码、DOI 未编造。正式使用前请以 CAJ 原文或知网导出数据核对，尤其 CN11/CN13 的年期及缺少的作者全表。确认后补齐字段，并删除 `note` 中的待核验提示、更新 `keywords`。
- 中文字体使用 TeX Live 自带 Fandol；英文正文沿用原字体。原 Reference 文件不修改。

## 引用键与原始资料对照

| 引用键 | 题名 | Reference 内来源 | 状态 |
| --- | --- | --- | --- |
| `REF01` | Is the Taklimakan Desert Highway Shelterbelt Sustainable to Long-Term Drip Irrigation with High Saline Groundwater? | 01_水盐与灌溉/01_水盐灌溉.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF02` | Moderate irrigation intervals facilitate establishment of two desert shrubs in the Taklimakan Desert Highway Shelterbelt in China | 01_水盐与灌溉/02_灌溉间隔.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF03` | Effects of Irrigation Regimes on Soil Water Dynamics of Two Typical Woody Halophyte Species in Taklimakan Desert Highway Shelterbelt | 01_水盐与灌溉/03_2022_灌溉制度与土壤水动态.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF04` | Spatial-Temporal Distribution of Soil Salt Crusts under Saline Drip Irrigation in an Artificial Desert Highway Shelterbelt | 01_水盐与灌溉/04_盐壳.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF05` | An Artificial Oasis in a Deadly Desert: Practices and Enlightenments | 01_水盐与灌溉/05_2022_人工绿洲工程综述_Opinion.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF06` | Ecologic Service, Economic Benefits, and Sustainability of the Man-Made Ecosystem in the Taklamakan Desert | 03_经济效益与动态优化/06_经济效益.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF07` | Vegetation against dune mobility | 02_风沙与灾害韧性/07_风沙植被.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF08` | Spatiotemporal dynamics of biocrust and vegetation on sand dunes | 02_风沙与灾害韧性/08_生物结皮.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF09` | A flow-kick model of dryland vegetation patterns: the impact of rainfall variability on resilience | 02_风沙与灾害韧性/09_随机降雨韧性.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF10` | A Pulsed-Precipitation Model of Dryland Vegetation Pattern Formation | 02_风沙与灾害韧性/10_脉冲降雨.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF11` | Crop Evapotranspiration Guidelines for Computing Crop Water Requirements | 01_水盐与灌溉/11_FAO56_作物蒸散指南_含2006勘误.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF12` | 3046公里“绿围脖”，护好塔克拉玛干沙漠 | 04_工程背景与数据入口/12_20241129_人民日报_锁边合龙.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF13` | 中国铁建和田地区沙漠边缘阻击战锁边固沙工程启动 | 04_工程背景与数据入口/13_于田项目.html | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF14` | 于田县塔克拉玛干沙漠锁边工程地下水水文地质勘探项目招标公告 | 04_工程背景与数据入口/14_地下水勘探.html | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF15` | ERA5-Land hourly data from 1950 to present | 04_工程背景与数据入口/15_ERA5Land.html | 本地PDF首页／资料索引；未补造缺失字段 |
| `REF16` | An Introduction to Trajectory Optimization: How to Do Your Own Direct Collocation | 03_经济效益与动态优化/16_动态优化方法.pdf | 本地PDF首页／资料索引；未补造缺失字段 |
| `CN01` | 京津风沙源区气候分异对植被和水文耦合效应的影响 | 01_水盐与灌溉/京津风沙源区气候分异对植被和水文耦合效应的影响_罗瑞新.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN02` | 人工固沙植被系统生态水文研究进展 | 01_水盐与灌溉/人工固沙植被系统生态水文研究进展_张亚峰.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN03` | 沙丘冻结表面风沙传输特征的风洞模拟研究 | 02_风沙与灾害韧性/沙丘冻结表面风沙传输特征的风洞模拟研究_李锦荣.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN04` | 塔克拉玛干沙漠不同地表输沙率和粒径特征 | 02_风沙与灾害韧性/塔克拉玛干沙漠不同地表输沙率和粒径特征_张文慧.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN05` | 交错和矩形布置对树状植被地表剪应力和输沙率的影响 | 02_风沙与灾害韧性/交错和矩形布置对树状植被地表剪应力和输沙率的影响_张萌.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN06` | 光伏电站建设的生态效应：光伏治沙研究进展与展望 | 03_经济效益与动态优化/光伏电站建设的生态效应：光伏治沙研究进展与展望_刘坤.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN07` | 沙漠地区光伏电站典型格状沙障防风固沙综合效益评估 | 03_经济效益与动态优化/沙漠地区光伏电站典型格状沙障防风固沙综合效益评估_猛克.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN08` | 塔里木河流域胡杨全生命周期生态需水规律 | 01_水盐与灌溉/塔里木河流域胡杨全生命周期生态需水规律_木塔里甫·托和提.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN09` | 基于遗传算法的宿迁黄河故道闸坝群生态补水调度多目标优化研究 | 03_经济效益与动态优化/基于遗传算法的宿迁黄河故道闸坝群生态补水调度多目标优化研究_李传龙.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN10` | 利益相关者参与内蒙古草原生态管理行动的四方演化博弈 | 03_经济效益与动态优化/利益相关者参与内蒙古草原生态管理行动的四方演化博弈_李雪敏.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN11` | 基于三层递阶结构模型的黑河中游大满灌区水资源优化配置 | 03_经济效益与动态优化/基于三层递阶结构模型的黑河中游大满灌区水资源优化配置_陈海牛.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN12` | 强沙尘暴下新能源基地的韧性评估及其提升方法 | 02_风沙与灾害韧性/强沙尘暴下新能源基地的韧性评估及其提升方法_王金岩.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN13` | 基于CMIP6气候变化下塔里木河流域天然植被生态需水预估 | 02_风沙与灾害韧性/基于CMIP6气候变化下塔里木河流域天然植被生态需水预估_黄娩婷.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN14` | 基于生态系统恢复力的干旱区植被生态需水阈值计算方法与应用 | 02_风沙与灾害韧性/基于生态系统恢复力的干旱区植被生态需水阈值计算方法与应用_雷逸甦.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN15` | 融合多源数据与机器学习的干旱区土壤水分降尺度方法——以宁夏为例 | 04_工程背景与数据入口/融合多源数据与机器学习的干旱区土壤水分降尺度方法——以宁夏为例_王兆一.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `CN16` | 基于NDVI动态监测的防护带时空演变及防沙治沙策略 | 04_工程背景与数据入口/基于NDVI动态监测的防护带时空演变及防沙治沙策略_蔡子良.caj | 待核验：作者全表、年期、卷号、页码、DOI |
| `EN01` | Plants in water-controlled ecosystems: active role in hydrologic processes and response to water stress: II. Probabilistic soil moisture dynamics | 05_英文补充与来源核验/（无本地全文，见 sources.json） | 沿用已有题录 |
| `EN02` | Parametrization of the increase of the aeolian erosion threshold wind friction velocity due to soil moisture for arid and semi-arid areas | 05_英文补充与来源核验/EN02_Fecan1999_Moisture_wind_threshold.pdf | 沿用已有题录 |
| `EN03` | A simple expression for wind erosion threshold friction velocity | 05_英文补充与来源核验/（无本地全文，见 sources.json） | 沿用已有题录 |
| `EN04` | Groundwater Depth and Soil Properties Are Associated with Variation in Vegetation of a Desert Riparian Ecosystem in an Arid Area of China | 05_英文补充与来源核验/EN04_Groundwater_vegetation2018.pdf | 沿用已有题录 |
| `EN05` | Study on the Impact of Large-Scale Photovoltaic Systems on Key Surface Parameters in Desert Area Regions of Xinjiang, China | 05_英文补充与来源核验/EN05_PV_microclimate_Xinjiang2025.pdf | 沿用已有题录 |
| `EN06` | Photovoltaic Degradation Rates—an Analytical Review | 05_英文补充与来源核验/EN06_PV_degradation_review2013.pdf | 沿用已有题录 |
| `EN07` | A Multiscalar Drought Index Sensitive to Global Warming: The Standardized Precipitation Evapotranspiration Index | 05_英文补充与来源核验/（无本地全文，见 sources.json） | 沿用已有题录 |
| `EN08` | NASA Global Daily Downscaled Projections, CMIP6 | 05_英文补充与来源核验/EN08_NEX_GDDP_CMIP6_2022.pdf | 沿用已有题录 |
| `EN09` | SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty | 05_英文补充与来源核验/EN09_SoilGrids2_2021.pdf | 沿用已有题录 |
| `EN10` | ERA5-Land: a state-of-the-art global reanalysis dataset for land applications | 05_英文补充与来源核验/EN10_ERA5_Land_method2021.pdf | 沿用已有题录 |
| `EN11` | Best Practices for Operation and Maintenance of Photovoltaic and Energy Storage Systems; 3rd Edition | 05_英文补充与来源核验/EN11_NREL_PV_OM_2018.pdf | 沿用已有题录 |
| `EN12` | Renewable power generation costs in 2025 | 05_英文补充与来源核验/EN12_IRENA_Costs2025_published2026.pdf | 沿用已有题录 |
| `EN13` | NEX-GDDP-CMIP6 (version 2) Technical Note | 05_英文补充与来源核验/EN13_NEX_GDDP_CMIP6_v2_TechNote2025.pdf | 沿用已有题录 |
| `EN14` | Effects of sand burial disturbance on establishment of three desert shrub species in the margin of oasis in northwestern China | 05_英文补充与来源核验/（无本地全文，见 sources.json） | 沿用已有题录 |
| `EN15` | Sandstorms cause shrinkage of Haloxylon ammodendron shrubs and limit their self-renewal | 05_英文补充与来源核验/EN15_Sandstorm_Haloxylon_damage2022.pdf | 沿用已有题录 |
| `EN16` | Effect of Straw Checkerboards on Wind Proofing, Sand Fixation, and Ecological Restoration in Shifting Sandy Land | 05_英文补充与来源核验/EN16_Straw_checkerboard2018.pdf | 沿用已有题录 |
