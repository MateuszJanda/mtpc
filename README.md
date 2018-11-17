# MTPC - many-time pad cracker

Simple application to crack "one-time pad" (now many-time pad) encrypted messages where secret key was reused multiple times.

There are two basic functions for cracking messages:
* `crack_blocks(enc_msgs, method, lang_stats, char_base)` - for cracking multiple block/separate messages, where length each of blocks is known, and secret key was reused for each of the blocks. Available parameters:
** `enc_msg` - list of encoded messages. Each character should be presented as int
** `method` - cracking method (**default:** `'space'`):
*** `'spaces'` - determine key by most common character (which is space in literature). Most common encrypted byte _e_ at give colon should the most common character _s_. We can retrieve key at this position by calculating _k = e ⊕ s_
*** `'best-freq'` - determine key by selecting xor-ed byte (_e1 ⊕ e2 = (k ⊕ m1)⊕(k ⊕ m2)=m1 ⊕ m2_) value with corresponding values in letters frequency table, with specific delta (**default:** 0.3)
*** `'first-order-freq'` - determine key by selecting xor-ed byte (_e1 ⊕ e2 = (k ⊕ m1)⊕(k ⊕ m2)=m1 ⊕ m2_) position in sorted table corresponding position in sorted letters frequency table.
** `lang_stats` - letters frequency distribution of specific language. **By default:** `mtpc.ENGLISH_LETTERS`
** `char_base`: characters expected in output message. **By default:** all Latin letters, space and apostrophe: `string.letters+" '"`

* `crack_stream(enc_msg, method, key_len_method, lang_stats, char_base, key_len_range, checks)` - for cracking one block/message, where secret key is significantly shorter than encrypted message, and was reused multiple times.
** `enc_msg` - encoded message. Each character should be encoded as int
** `method` - cracking method (**default:** `'space'`):
*** `'spaces'` - determine key by most common character (which is space in literature). Most common encrypted byte _e_ at give colon should the most common character _s_. We can retrieve key at this position by calculating _k = e ⊕ s_
*** `'best-freq'` - determine key by selecting xor-ed byte (_e1 ⊕ e2 = (k ⊕ m1)⊕(k ⊕ m2)=m1 ⊕ m2_) value with corresponding values in letters frequency table, with specific delta (**default:** 0.3)
*** `'first-order-freq'` - determine key by selecting xor-ed byte (_e1 ⊕ e2 = (k ⊕ m1)⊕(k ⊕ m2)=m1 ⊕ m2_) position in sorted table corresponding position in sorted letters frequency table.
** `key_len_method` - method to determine key length (**default:** `'high-bits'`)
*** `'hamming'` - Hamming distance to determine key length
*** `'high-bits'` - works only when key contain high bits (key is not build from printable characters)
** `lang_stats` - letters frequency distribution of specific language. **By default:** `mtpc.ENGLISH_LETTERS`
** `key_len_range` - to reduce the number of combinations `key_len_range` can be provided. **By default:** `range(2, 100)`
** `checks` - number of best result to show. **By default:** 5

## Examples
```
[+] Testing block cracking
Number of combinations: 382321831366549831680
Keys counts: *21221111111221111222112222221211111111111211112112212111111111211211111111111111211211121211222222*12117122312122111186171111127115422
Index......: 012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234
Plain.....0: Gi f N__ York C_t_ dh_rshoute_a__ur_ ____ei_es_celiber____g ___'_ase_o____ ___y_au__ld__hy f_oj'a'spum_ on srial'a__ aboecef_y tr__coe
Plain.....1: Ga she__ is any_r_ath_aele co_b__th_y____ s_ r_surn a ____ic___a_not_g____y___f_fh__d __nlty_ soe'bsy _ill ueceiqb__ dkbtl q_ntbh__
Plain.....2: Gi f p__liminar_ _osb_ fll mu_o__ v_t____un_ty_'except____or___'_ho _r____ ___t_to__bo__cese_vbt toqe _elibbratihi_
Plain.....3: Zoit i__itates _o_e'h_ she ht_e__ju_o____wo_ a_b impat____ f___f_qui_k____i___a_ih__
Plain.....4: ktpbci__ly Juro_ _ po_ oas si_k__s _o____ b_en_ig's Ya____s ___b_ an_ ____h___e_oi__ra__t bl_tfit'pnej_dice'agaiit__peasla d_om'u__lu
Plain.....5: Drrhr __questio_s_tob_adcurfc_ __d _e____ik_ty_hf the ____ t___p_tne_s____a___t_e'__os__rtio_'t'ckaum _hat she mru__r yfatol_
Plain.....6: o'chmm__ switch_l_db'_oa whnc_ __ p_s____et_an_ndentic____op___'_as _r____
Plain.....7: Drrhr __argues _h_t'u_atonael_ __ub_ ____tt_ a_c that ____he___h_e c_n____v___ _gr__ty__'but_chicbdys _hat oe hat'__rebz lul_ toc__ttri
Plain.....8: Drrhr __suggest_ _ tb_rbt bfl_o__ f_o____id_ h_'will a____in___i_ ag_e____o___a_gb__is__hte _f'shb sth_rs uianimhr__y xlta  _uikr__
Plain.....9: Zoe'ba__ot is h_l_ fi_ f nep _n__ g_i____ q_te_fppears_
Plain....10: Oi fng__ Juror _ _cdr_et Juuo_ __ w_o____w'_p _i a slu____f ___i_ing_h____o___o_t'__ s__wath_ shwfrxs _lum dhildub__
Plain....11: Fhwbve__ Juror _ _eqb_lt it'w_s__e _h____hf_ge_'his vo____ag___n_g t_e____h___d_bb__om__cisc_stnoi
Plain....12: Drrhr __argues _h_t's_e'noite_o__a _a____g'_ra_i would____e ___d_red_t____e___l_to__at__oat _nb'wntres_ clanmed sh_
Plain....13: ffvb h__rd the _o_ sb_l'his'f_t__r _I____on_g _h kill ____
Plain....14: Drrhr __then ch_n_et'_it vose_ __ro_ ____lt_ c_fnges h____ot___
Plain....15: lblnev__g the b_y_whr_d'not'l_k__y _a____rn_d _h retri____th___r_der_w____n___o_ s__ s__ie i_ ns oax b_en ckeanec'__ fgmgarr_insu_
Key (str)..: ?bvbr __nd a hu_a_ sh_dh a ja_h__e'_ ____eq_r _bnd a h____ t___h_a m_c____'___o_Nb__r __id a_hrjai ho _o a jachiib__ jaaNavg_ sbh__??c?
Key (hex)..: 406276627220____6e642061206875__61__207368__64682061206a61__68____6527__20________6571__7220__626e6420612068________2074______68__61206d__63________27______6f__4e62____7220____69642061__68726a616920686f20__6f2061206a616368696962____206a61614e617667__20736268____60266332
End check
```
