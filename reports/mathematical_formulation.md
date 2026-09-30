# Code-Matching Mathematical Formulation

This document specifies the planning approximation implemented in
`src/acdc_boundary/model.py`. It is descriptive of the code, including its
deliberate simplifications, rather than a more physically complete surrogate.

## Network and scenario data

Let \(G=(V,E)\) be a rooted radial tree with transformer-side root \(r\). Each
directed edge \(e=(i,j)\) points from parent \(i\) to child \(j\). For every bus
\(i\), the frozen scenario provides annual endpoint energy \(E_i\), peak endpoint
power \(P_i\), and native-DC energy share \(q_i\in[0,1]\). For every edge, the
preprocessor provides length \(\ell_e\), resistance per kilometre \(\rho_e\),
ampacity \(\bar I_e\), downstream annual energy \(E_e^\downarrow\), downstream
peak power \(P_e^\downarrow\), and equivalent loss hours \(H_e\).

Portfolio multipliers \(f_E\) and \(f_P\) scale annual energy and peak power,
respectively. The downstream quantities are fixed before optimization; converter
losses and line losses do not feed back into upstream power. This separability is
essential to the exact dynamic program.

## Decisions

The root is fixed AC. Each non-root bus has domain
\(d_i\in\{\mathrm{AC},\mathrm{DC}\}\) when DC is permitted, or
\(d_i=\mathrm{AC}\) in an AC-only cell. Edge \(e=(i,j)\) takes its downstream
bus domain \(d_j\). Each edge selects a conductor multiplier
\(s_e\in S=\{1,1.5,2\}\) in conductor-optimized cells; fixed-conductor cells use
\(s_e=1\).

A boundary converter is present on \(e=(i,j)\) exactly when
\(d_i\ne d_j\). “Root-converted DC” means every non-root bus is DC and the only
domain transition is at the root edge or root edges. “Hybrid” means at least one,
but not all, non-root buses are DC.

## Electrical quantities

The scaled series resistance is

\[
R_e(s_e)=\rho_e\ell_e/s_e .
\]

With line-to-line AC voltage \(V_{\mathrm{AC}}\), pole-to-pole DC voltage
\(V_{\mathrm{DC}}\), and AC power factor \(\mathrm{pf}\), the coded peak currents
are

\[
I_e^{\mathrm{AC}}=
\frac{1000 f_P P_e^\downarrow}
{\sqrt{3}V_{\mathrm{AC}}\mathrm{pf}},
\qquad
I_e^{\mathrm{DC}}=
\frac{1000 f_P P_e^\downarrow}{V_{\mathrm{DC}}}.
\]

Annual line loss is

\[
L^{\mathrm{line}}_e(d_j,s_e)=
\begin{cases}
3(I_e^{\mathrm{AC}})^2R_e(s_e)H_e/1000, & d_j=\mathrm{AC},\\
2(I_e^{\mathrm{DC}})^2R_e(s_e)H_e/1000, & d_j=\mathrm{DC}.
\end{cases}
\]

The factor \(1000\) converts watts to kilowatts. The AC expression represents
three phase conductors; the DC expression represents two loaded poles. This is a
balanced active-power screening approximation, not an unbalanced power-flow
model.

## Endpoint and boundary conversion

Let \(z_i=1\) for DC and \(0\) for AC. The endpoint energy requiring conversion is

\[
E_i^{\mathrm{mis}}=
f_E E_i\{z_i(1-q_i)+(1-z_i)q_i\}.
\]

For endpoint efficiency \(\eta_{\mathrm{end}}\),

\[
L_i^{\mathrm{end}}=
E_i^{\mathrm{mis}}(\eta_{\mathrm{end}}^{-1}-1).
\]

For boundary efficiency \(\eta_b\) and standby fraction \(\sigma_b\), the coded
boundary electrical loss is

\[
L_e^{\mathrm{boundary}}=
\mathbf{1}[d_i\ne d_j]
\left[
f_EE_e^\downarrow(\eta_b^{-1}-1)
+\sigma_b f_PP_e^\downarrow 8760
\right].
\]

The associated converter-capacity index is

\[
C_e=\mathbf{1}[d_i\ne d_j]f_PP_e^\downarrow .
\]

The model applies the same efficiency convention in either conversion direction.
It has no chronological direction reversal, part-load curve, loss feedback,
reactive-power exchange, or converter redundancy.

## Material and total objective

The normalized conductor-material index is

\[
M_e(d_j,s_e)=n(d_j)\ell_es_e,\qquad
n(\mathrm{AC})=4,\quad n(\mathrm{DC})=3.
\]

This is a scenario index, not a bill of materials or cost. In particular, it does
not establish universal equivalence among AC neutral/earth and bipolar-DC
return/grounding requirements.

Total modeled electrical loss is

\[
L_{\mathrm{tot}}=
\sum_{e\in E}L_e^{\mathrm{line}}+
\sum_{i\in V}L_i^{\mathrm{end}}+
\sum_{e\in E}L_e^{\mathrm{boundary}}.
\]

The optimized score is

\[
J=L_{\mathrm{tot}}+
\lambda_M\sum_{e\in E}M_e+
\lambda_C\sum_{e\in E}C_e .
\]

\(\lambda_M\) and \(\lambda_C\) are normalized regularization weights. They are
not currency-valued equipment costs. The manuscript therefore reports electrical
loss and each regularizer separately and does not interpret \(J\) as lifecycle
economics.

## Post-optimization diagnostics

The ampacity-utilization diagnostic is

\[
u_e=\frac{I_e(d_j)}{\bar I_es_e}.
\]

The single-edge voltage-drop diagnostic matches the implementation:

\[
\delta_e=
\begin{cases}
I_e^{\mathrm{AC}}R_e/(V_{\mathrm{AC}}/\sqrt{3}), & d_j=\mathrm{AC},\\
I_e^{\mathrm{DC}}R_e/(V_{\mathrm{DC}}/2), & d_j=\mathrm{DC}.
\end{cases}
\]

Configured limits flag results after optimization. They are not feasibility
constraints in the dynamic program; “exact” never means exact for a constrained
unbalanced network-design problem.

## Dynamic program

For a bus \(i\) and fixed domain \(d\), let \(F_i(d)\) be the minimum objective
contribution of the subtree rooted at \(i\), including endpoint conversion at
\(i\), all descendant edges and endpoints, and every boundary internal to that
subtree. The local endpoint term is \(L_i^{\mathrm{end}}(d)\). For child
\(j\in\mathcal C(i)\),

\[
F_i(d)=L_i^{\mathrm{end}}(d)+
\sum_{j\in\mathcal C(i)}
\min_{\substack{d'\in D\\s\in S}}
\left[
F_j(d')+
L_{ij}^{\mathrm{line}}(d',s)+
\lambda_MM_{ij}(d',s)+
\mathbf{1}[d\ne d']
\{L_{ij}^{\mathrm{boundary}}+\lambda_CC_{ij}\}
\right].
\]

For a leaf, \(F_i(d)=L_i^{\mathrm{end}}(d)\). The reported optimum is
\(F_r(\mathrm{AC})\). Backtracking stored child-domain and conductor choices
recovers the architecture and conductor multipliers. Iteration order is AC before
DC and increasing conductor multiplier; exact floating-point ties therefore
select AC and then the smaller multiplier. Independent validation treats all
solutions within a declared numerical tolerance as tied and requires architecture
agreement only for unique optima.

With \(|D|\) domain states and \(|S|\) conductor choices, the algorithm computes
\(O(|V||D|)\) states and \(O(|E||D|^2|S|)\) transition/conductor evaluations, with
\(O(|V||D|+|E||D|)\) stored values and decisions. Here \(|D|\le2\) and
\(|S|\le3\), so runtime is linear in feeder size for the declared approximation.

## Exactness boundary

The recursion is exact because, conditional on a bus domain, child-subtree costs
are additive and downstream profiles are fixed. Exactness does not extend to
coupled voltage constraints, meshed operation, converter-loss feedback,
chronological storage dispatch, unbalance, reactive power, harmonics, protection,
reliability, or economic deployment.
