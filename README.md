# October
1.以key_words为性能bug的关键词，szz溯源找到buggy_commit

2.由commit_hash进行特征扩展，得到project	parent_hashes	commit_hash	author_name	author_email	author_date	author_date_unix_timestamp	commit_message	la	ld	fileschanged	nf	ns	nd	entropy	ndev	lt	nuc	age	exp	rexp	sexp	classification	fix	is_buggy_commit

3.获取tensorflow，pytorch，szz，cvc5等多个受欢迎仓库的特征值数据集，进行JIT实验复现

4.JIT实验基线复现包含LApredict，Deeper，jitfine，cct5

code文件夹解释：

001-006.py：

扩展特征值，得到project parent_hashes commit_hash author_name author_email author_date author_date_unix_timestamp commit_message la ld fileschanged nf ns nd entropy ndev lt nuc age exp rexp sexp classification fix is_buggy_commit

all_id.py:列举所有hash值

choose_id1.py:从szz结果json文件中找到是commit_bug的hash值

choose_id0.py:从szz结果json文件中找到不是commit_bug的hash值

change_suffix.py:更改后缀，快速更换仓库路径

merge.py:按顺序得到完整数据列表

