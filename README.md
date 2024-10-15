# October
以key_words为性能bug的关键词，szz溯源找到buggy_commit
由commit_hash进行特征扩展，得到project	parent_hashes	commit_hash	author_name	author_email	author_date	author_date_unix_timestamp	commit_message	la	ld	fileschanged	nf	ns	nd	entropy	ndev	lt	nuc	age	exp	rexp	sexp	classification	fix	is_buggy_commit
获取tensorflow，pytorch，szz，cvc5等多个受欢迎仓库的特征值数据集，进行JIT实验复现
JIT实验基线复现包含LApredict，Deeper，jitfine，cct5
