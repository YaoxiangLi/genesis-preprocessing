x <- readRDS('/data/atlas.RDS')
m <- attr(x,'meta.data')
print(class(x));print(dim(m));print(colnames(m));print(attr(x,'version'))
write.table(cbind(barcode=rownames(m),m),'/out/author-cells.tsv',sep='\t',row.names=FALSE,quote=FALSE)
a <- attr(x,'assays')
for (n in names(a)) {
 fs<-attr(a[[n]],'fragments')
 if(!is.null(fs)) for(i in seq_along(fs)) {
  print(list(assay=n,index=i,path=attr(fs[[i]],'path'),hash=attr(fs[[i]],'hash')))
  cs<-attr(fs[[i]],'cells')
  if(!is.null(cs)) write.table(data.frame(cell_id=names(cs),source_barcode=as.character(cs)),paste0('/out/',n,'-',i,'-barcode-map.tsv'),sep='\t',row.names=FALSE,quote=FALSE)
 }
}
