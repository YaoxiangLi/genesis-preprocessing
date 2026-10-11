c <- gzcon(gzfile('/data/combined.RData.gz','rb'));load(c);close(c)
x <- sorghum_multiome_RNA_combined
id <- attr(x,'active.ident')
write.table(data.frame(cell_id=names(id),author_active_label=as.character(id)),'/out/active-labels.tsv',sep='\t',row.names=FALSE,quote=FALSE)
print(table(id))
f <- attr(attr(x,'assays')[['ATAC']],'fragments')
for (i in seq_along(f)) {
 cs<-attr(f[[i]],'cells')
 print(list(index=i,path=attr(f[[i]],'path'),cells=length(cs)))
 write.table(data.frame(cell_id=names(cs),source_barcode=as.character(cs)),paste0('/out/barcode-map-',i,'.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
}
if(file.exists('/sys/fs/cgroup/memory.peak'))print(readLines('/sys/fs/cgroup/memory.peak'))
