# Emotional Anticipation Task — Scientific Rationale
### Mind After Midnight Study | Sleep and Health Research Program
### Department of Psychiatry, University of Arizona

---

## Overview

This document describes the scientific rationale, theoretical background, and
psychophysiological significance of the Emotional Anticipation Task (EAT) as
implemented for the Mind After Midnight (MaM) study. For installation and
technical documentation, see README.md.

---

## The Mind After Midnight Study

The Mind After Midnight study is a clinical research investigation examining how
nocturnal wakefulness — being awake between approximately 1am and 4am — affects
cognitive control, emotional processing, and suicide risk. The study administered
a comprehensive neuropsychological battery at multiple timepoints across the
circadian cycle (morning, evening, and overnight) to characterize how performance
on cognitive and affective tasks fluctuates with time of day in individuals with
varying histories of suicidal ideation.

The EAT was the final component of the psychophysiological portion of the battery,
administered while participants remained connected to EEG/PSG recording equipment.

---

## What the EAT Measures

The Emotional Anticipation Task is a cognitive-affective paradigm designed to
evaluate brain activation associated with anticipating emotionally valenced stimuli.
The task targets the anticipatory phase of emotional processing — what happens in
the brain and behavior in the seconds before an emotional stimulus arrives — rather
than the response to the stimulus itself.

### Trial Structure

Each trial presents the following sequence:

1. **Baseline arrow display** — A black arrow pointing left or right on a grey
   background. Participants indicate the direction via button press. This serves
   as a baseline cognitive condition and attention check.

2. **Color cue** — The screen color changes to signal the valence of the upcoming
   image:
   - **Yellow** → A negative image is coming (certain threat anticipation)
   - **Blue** → A positive image is coming (certain reward anticipation)
   - **Green** → Either a positive or negative image may appear (uncertain
     anticipation)

3. **Anticipation period** — 6 seconds of sustained anticipation following the
   color cue, regardless of condition.

4. **Image presentation** — A positive or negative image from the International
   Affective Picture System (IAPS), presented for 2 seconds.

Each anticipation condition (certain threat, certain reward, uncertain) is tested
9 times in pseudorandom order across approximately 90 trials. Total time on task
is approximately 15 minutes.

---

## Psychophysiological Targets

The EAT was specifically designed to elicit two well-characterized ERP components
that index anticipatory and reactive emotional processing:

### Stimulus Preceding Negativity (SPN)

The SPN is a slow, negative-going ERP component that emerges during the
anticipatory period — the interval between the cue and the upcoming emotional
stimulus.

| Feature | Description |
|---------|-------------|
| Latency | Begins approximately 500–1000 ms before anticipated stimulus onset |
| Duration | Builds gradually during the cue-target interval (typically 2–4 seconds) |
| Topography | Most prominent over fronto-central scalp regions (FCz, Cz) |
| Polarity | Negative deflection relative to baseline or neutral anticipation |

Larger SPN amplitudes are observed when the upcoming stimulus is emotionally
charged, uncertain or anxiety-provoking, or behaviorally relevant (reward,
punishment, performance feedback). In the MaM study context, SPN amplitude
during overnight testing was expected to reflect altered anticipatory processing
under conditions of circadian disruption and sleep deprivation.

### Late Positive Potential (LPP)

The LPP is a sustained, positive-going ERP component reflecting enhanced
attentional and emotional processing of affectively salient stimuli after they
appear.

| Feature | Description |
|---------|-------------|
| Latency onset | Begins approximately 300–400 ms after stimulus presentation |
| Duration | Can last 1000–6000 ms depending on stimulus duration and task |
| Scalp topography | Maximal at centro-parietal sites (CPz, Pz) |
| Amplitude sensitivity | Scales with arousal intensity regardless of valence |
| Task independence | Elicited even in passive viewing — no overt response required |

LPP amplitude provides a robust index of motivated attention and emotional
arousal, making it well-suited to characterizing how affective reactivity
fluctuates across circadian phases.

---

## Relevance to Nocturnal Suicidality

The EAT was selected for the MaM battery based on a convergence of evidence
linking nocturnal wakefulness, anticipatory cognition, and suicide risk:

**Nighttime rumination** — Rumination during nocturnal wakefulness involves
repetitive, negatively skewed forecasting about the future. The anticipatory
structure of the EAT directly probes this forward-looking affective processing.

**Anticipatory anxiety under fatigue** — Anticipatory anxiety tends to increase
during circadian troughs and under conditions of sleep deprivation, potentially
amplifying aversive anticipatory states at 3am relative to morning or evening
testing.

**Suicidal cognition and future orientation** — Suicidal thinking characteristically
involves future-oriented emotional scenarios — imagining escape, social fallout,
consequences, and guilt. The EAT's anticipatory structure maps directly onto this
cognitive pattern.

**Impaired nocturnal cognitive control** — Reduced cognitive control at night may
impair the modulation of aversive anticipation, resulting in affective overload
that cannot be adequately regulated under circadian stress.

---

## Role in the Broader Battery

The EAT occupied a specific position in the MaM battery — administered after the
Eriksen Flanker Task, while EEG recording continued. This sequencing was deliberate:

- The Flanker Task established baseline ERN and frontal midline theta (FMT) measures
  reflecting ACC function and cognitive control integrity
- The EAT then probed whether those same ACC networks, already characterized at rest
  and during cognitive control, showed differential recruitment during anticipatory
  emotional processing

Together, the Flanker and EAT provided complementary EEG windows into ACC function —
the Flanker through error monitoring and cognitive control, the EAT through
anticipatory emotional regulation — across the same participants at the same
circadian phases.

---

## Stimulus Materials

Emotional images were drawn from the **International Affective Picture System (IAPS)**,
a standardized, normatively validated set of emotional photographs widely used in
affective neuroscience research. IAPS images are not included in this repository
as they are licensed materials distributed by the Center for the Study of Emotion
and Attention (CSEA) at the University of Florida.

Researchers wishing to use this task should obtain IAPS access through official
channels: https://csea.phhp.ufl.edu/media/iapsmessage.html

---

## Key References

Watson, D., Clark, L. A., & Tellegen, A. (1988). Development and validation of
brief measures of positive and negative affect: The PANAS scales. *Journal of
Personality and Social Psychology*, 54(6), 1063–1070.

Kotchubey, B. (2006). Event-related potential measures of consciousness: Two
equations with three unknowns. *Progress in Brain Research*, 150, 427–444.

Hajcak, G., MacNamara, A., & Olvet, D. M. (2010). Event-related potentials,
emotion, and emotion regulation: An integrative review. *Developmental
Neuropsychology*, 35(2), 129–155.

Van Voorhis, A. C. W., & Eaton, N. R. (2022). The role of anticipatory affect in
emotional disorders: A meta-analytic review. *Clinical Psychology Review*, 92,
102121.

---

## Citation

If you use or adapt this task in your research, please cite the Mind After Midnight
study and this repository:

Sangpo, S. (2025). *Emotional Anticipation Task — Mind After Midnight Study*
[Software]. Sleep and Health Research Program, Department of Psychiatry,
University of Arizona. https://github.com/SurZen/emotional-anticipation-task
